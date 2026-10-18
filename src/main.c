/* Experimental Dragon Quest VIII disc launcher.
 * Reset syscall trampolines adapted from PS2rd (GPL-3.0-or-later).
 * This file is distributed under GPL-3.0-or-later.
 * Uses the user's disc and patches temporary RAM only.
 */
#include <tamtypes.h>
#include <kernel.h>
#include <sifrpc.h>
#include <sifcmd.h>
#include <sifdma.h>
#include <iopcontrol.h>
#include <iopheap.h>
#include <loadfile.h>
#include <sbv_patches.h>
#include <debug.h>
#include <libcdvd.h>
#include <fileio.h>
#include <syscallnr.h>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
extern unsigned char usbd_data[],pademu_data[],xbox_data[];
extern unsigned int usbd_size,pademu_size,xbox_size;
extern u32 (*OldSifSetDma)(SifDmaTransfer_t *,s32);
extern int (*OldSifSetReg)(u32,int);
extern void HookSifSetDma(void),HookSifSetReg(void);
extern int _iop_reboot_count;
extern char _end[];
static u8 stage_buffer[32768] __attribute__((aligned(64)));
static volatile unsigned reset_count,bridge_stage;
static int skip_registers,inside_reset;
static const char boot_path[]="cdrom0:\\SLES_539.74;1";
static unsigned char boot_cnf[1024] __attribute__((aligned(64)));
static char *game_args[]={(char *)boot_path,NULL};
static void color(unsigned int rgb){*(volatile unsigned long long *)0x120000e0=rgb;}
static void fatal(unsigned int code){
 bridge_stage=code;color(0x000000ff);
 /* Fail in temporary RAM. A normal power-off removes the hooks. */
 for(;;)__asm__ volatile("nop");
}
static u32 old_dma(SifDmaTransfer_t *d,s32 n){
 u32 result;DIntr();ee_kmode_enter();result=OldSifSetDma(d,n);ee_kmode_exit();EIntr();return result;
}
static int old_reg(u32 reg,int value){
 int result;DIntr();ee_kmode_enter();result=OldSifSetReg(reg,value);ee_kmode_exit();EIntr();return result;
}
static int load_blob(const unsigned char *src,unsigned int len,unsigned int marker,void *mailbox,int argc,const char *args){
 if(len>sizeof(stage_buffer))return -900;
 memcpy(stage_buffer,src,len);
 if(marker){
  unsigned int found=0;
  for(unsigned int i=0;i+4<=len;i++){
   unsigned int word;memcpy(&word,stage_buffer+i,4);
   if(word==marker){word=(unsigned int)mailbox;memcpy(stage_buffer+i,&word,4);found++;}
  }
  if(found!=1)return -901;
 }
 int result=-999,id=SifExecModuleBuffer(stage_buffer,len,argc,args,&result);
 return id<0?id:result;
}
static int install_bridge(void){
 bridge_stage=10;
 SifInitRpc(0);SifLoadFileInit();SifInitIopHeap();
 sbv_patch_enable_lmb();sbv_patch_disable_prefix_check();
 void *trace=SifAllocIopHeap(64),*usb=SifAllocIopHeap(256);
 if(!trace || !usb)return -910;
 /* Initialize mailboxes with DMA through an allocated staging buffer. */
 memset(stage_buffer,0,256);SifWriteBackDCache(stage_buffer,256);
 SifDmaTransfer_t d={stage_buffer,trace,64,0};
 unsigned int q=SifSetDma(&d,1);if(!q)return -911;while(SifDmaStat(q)>=0){}
 d.dest=usb;d.size=256;q=SifSetDma(&d,1);if(!q)return -912;while(SifDmaStat(q)>=0){}
 bridge_stage=11;
 int r=load_blob(usbd_data,usbd_size,0,NULL,0,NULL);if(r!=0)return r;
 bridge_stage=12;
 const char options[4]={1,0,0,0};
 r=load_blob(pademu_data,pademu_size,0x1badb002,trace,4,options);if(r!=0)return r;
 bridge_stage=13;
 r=load_blob(xbox_data,xbox_size,0x1badb003,usb,0,NULL);if(r!=0)return r;
 bridge_stage=14;return 0;
}
/* Called in normal user context after PS2rd's syscall EPC trampoline returns. */
u32 NewSifSetDma(SifDmaTransfer_t *dma,s32 count){
 if(inside_reset)return old_dma(dma,count);
 inside_reset=1;color(0x00800080);
 /* Send the game's original reset packet and original IOPRP path unmodified. */
 u32 result=old_dma(dma,count);
 if(!result){inside_reset=0;return 0;}
 _iop_reboot_count++;reset_count++;
 old_reg(SIF_REG_SMFLAG,SIF_STAT_SIFINIT);
 old_reg(SIF_REG_SMFLAG,SIF_STAT_CMDINIT);
 old_reg(SIF_SYSREG_RPCINIT,0);
 old_reg(SIF_SYSREG_SUBADDR,0);
 while(!SifIopSync()){}
 /* Clear our old clients after the reset; game RPC has not rebound yet. */
 SifLoadFileExit();SifExitIopHeap();SifExitRpc();
 int r=install_bridge();if(r!=0)fatal(bridge_stage);
 SifLoadFileExit();SifExitIopHeap();SifExitRpc();
 skip_registers=4;inside_reset=0;color(0);return 1;
}
int NewSifSetReg(u32 reg,int value){
 if(skip_registers){skip_registers--;return 0;}
 return old_reg(reg,value);
}
static int validate_elf(const char *path){
 unsigned char hdr[52];int fd=fioOpen(path,O_RDONLY);if(fd<0)return -1;
 if(fioRead(fd,hdr,52)!=52 || memcmp(hdr,"\177ELF",4) || hdr[4]!=1 || hdr[5]!=1){fioClose(fd);return -2;}
 unsigned int phoff;unsigned short phsize,phnum;
 memcpy(&phoff,hdr+28,4);memcpy(&phsize,hdr+42,2);memcpy(&phnum,hdr+44,2);
 if(phsize!=32 || phnum==0 || phnum>32){fioClose(fd);return -3;}
 int loads=0;
 for(unsigned int i=0;i<phnum;i++){
  unsigned int ph[8];if(fioLseek(fd,phoff+i*32,SEEK_SET)<0 || fioRead(fd,ph,32)!=32){fioClose(fd);return -4;}
  if(ph[0]!=1)continue;
  unsigned int address=ph[2]&0x1fffffff;
  /* Keep the resident code below 1 MiB and the active loader stack above 31 MiB. */
  if(address<0x00100000 || address>=0x01f00000 || ph[5]>0x01f00000-address || ph[4]>ph[5]){fioClose(fd);return -5;}
  loads++;
 }
 fioClose(fd);return loads?0:-6;
}
int main(void){
 init_scr();scr_setCursor(0);
 scr_printf("\nDRAGON QUEST VIII DISC + KINHANK v11\nExperimental game-launch test. Temporary RAM only.\n\n");
 scr_printf("Resident CRT and screen initialized.\nInitializing RPC...\n");
 SifInitRpc(0);
 scr_printf("Resetting IOP...\n");while(!SifIopReset("",0)){}while(!SifIopSync()){}
 SifInitRpc(0);SifLoadFileInit();SifInitIopHeap();
 if(!sceCdInit(SCECdINIT)){scr_printf("Disc initialization failed.\n");SleepThread();return 0;}
 scr_printf("Waiting for Dragon Quest VIII disc...\n");sceCdDiskReady(0);
 int fd=fioOpen("cdrom0:\\SYSTEM.CNF;1",O_RDONLY);
 if(fd<0){scr_printf("Cannot read disc SYSTEM.CNF (%d).\n",fd);SleepThread();return 0;}
 int n=fioRead(fd,boot_cnf,sizeof(boot_cnf)-1);fioClose(fd);
 if(n<0){scr_printf("Disc read failed.\n");SleepThread();return 0;}
 boot_cnf[n]=0;
 if(!strstr((char *)boot_cnf,"SLES_539.74")){scr_printf("This build requires SLES_539.74. Disc contents:\n%s\n",boot_cnf);SleepThread();return 0;}
 scr_printf("Disc identified: SLES_539.74 (PAL).\n");
 int checked=validate_elf(boot_path);
 if(checked){scr_printf("Game ELF validation failed: %d\n",checked);SleepThread();return 0;}
 scr_printf("Loading original disc executable...\n");
 t_ExecData elf;memset(&elf,0,sizeof(elf));
 int loaded=SifLoadElf(boot_path,&elf);
 if(loaded || !elf.epc){scr_printf("Disc ELF load failed: %d, entry=%08X\n",loaded,elf.epc);SleepThread();return 0;}
 scr_printf("Game entry: %08X. Installing USB bridge...\n",elf.epc);
 int r=install_bridge();
 if(r){scr_printf("Bridge load failed: stage %u result %d\n",bridge_stage,r);SleepThread();return 0;}
 scr_printf("Bridge loaded. Installing reset hooks...\n");
 SifLoadFileExit();SifExitIopHeap();SifExitRpc();
 OldSifSetDma=GetSyscallHandler(__NR_SifSetDma);OldSifSetReg=GetSyscallHandler(__NR_SifSetReg);
 SetSyscall(__NR_SifSetDma,HookSifSetDma);SetSyscall(__NR_SifSetReg,HookSifSetReg);
 scr_printf("Starting game from disc.\nPink during IOP reset; red means the hook stopped.\n");
 FlushCache(0);FlushCache(2);color(0);
 ExecPS2((void *)elf.epc,(void *)elf.gp,1,game_args);
 fatal(99); /* Do not exit with resident hooks still installed if ExecPS2 fails. */
 return 0;
}
