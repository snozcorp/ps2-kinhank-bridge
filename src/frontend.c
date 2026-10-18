/* Standard-address bootstrap for the resident disc launcher. GPL-3.0-or-later. */
#include <tamtypes.h>
#include <kernel.h>
#include <debug.h>
#include <string.h>
#include <unistd.h>
#include <sifrpc.h>
#include <loadfile.h>
#include <iopheap.h>
extern unsigned char resident_elf[];
extern unsigned int resident_size,resident_main,resident_gp;

typedef struct {unsigned char ident[16];unsigned short type,machine;unsigned int version,entry,phoff,shoff,flags;unsigned short ehsize,phentsize,phnum,shentsize,shnum,shstrndx;} ElfHeader;
typedef struct {unsigned int type,offset,vaddr,paddr,filesz,memsz,flags,align;} ProgramHeader;
static int copy_resident(void){
 if(resident_size<sizeof(ElfHeader))return -1;
 ElfHeader *h=(ElfHeader*)resident_elf;
 if(memcmp(h->ident,"\177ELF",4) || h->ident[4]!=1 || h->ident[5]!=1 || h->phentsize!=32 || h->phnum>16)return -2;
 if(h->phoff>resident_size || h->phnum>(resident_size-h->phoff)/32)return -3;
 int count=0;
 for(unsigned int i=0;i<h->phnum;i++){
  ProgramHeader *p=(ProgramHeader*)(resident_elf+h->phoff+i*32);
  if(p->type!=1)continue;
  if(p->vaddr<0x90000 || p->vaddr>=0x100000 || p->memsz>0x100000-p->vaddr || p->filesz>p->memsz)return -4;
  if(p->offset>resident_size || p->filesz>resident_size-p->offset)return -5;
  count++;
 }
 if(!count || resident_main<0x90000 || resident_main>=0x100000)return -6;
 for(unsigned int i=0;i<h->phnum;i++){
  ProgramHeader *p=(ProgramHeader*)(resident_elf+h->phoff+i*32);
  if(p->type!=1)continue;
  memcpy((void*)p->vaddr,resident_elf+p->offset,p->filesz);
  if(memcmp((void*)p->vaddr,resident_elf+p->offset,p->filesz))return -7;
  memset((void*)(p->vaddr+p->filesz),0,p->memsz-p->filesz);
 }
 FlushCache(0);FlushCache(2);return 0;
}
int main(void){
 init_scr();scr_setCursor(0);
 scr_printf("\nDQ8 + KINHANK V11 STARTUP\nNormal ELF startup reached.\n\n");
 scr_printf("Preparing resident disc loader...\n");
 int r=copy_resident();
 if(r){scr_printf("Resident image validation failed: %d\n",r);SleepThread();return 0;}
 extern void checkpoint_hold(void);
 checkpoint_hold();
 scr_printf("Resident copy verified. Starting clean runtime...\n");
 /* No timed sleep or frontend RPC initialization: neither is needed.
    ExecPS2 retires frontend threads; CRT initializes the resident SDK/libc. */
 FlushCache(0);FlushCache(2);
 ExecPS2((void*)resident_main,NULL,0,NULL);
 scr_printf("ExecPS2 returned unexpectedly. Power off normally.\n");
 SleepThread();return 0;
}
