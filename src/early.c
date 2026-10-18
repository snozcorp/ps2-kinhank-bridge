#include <tamtypes.h>
#include <debug.h>
/* Avoid optional ROM-based timezone initialization before the first checkpoint. */
void _libcglue_timezone_update(void) {}
void _libcglue_rtc_update(void) {}
unsigned char entry_stack[8192] __attribute__((aligned(128)));
static void hold(void) {
 unsigned int start,now;
 __asm__ volatile("mfc0 %0,$9":"=r"(start));
 do {__asm__ volatile("mfc0 %0,$9":"=r"(now));}while((unsigned int)(now-start)<294912000u);
}
void early_screen(void) {
 init_scr();scr_setCursor(0);
#ifdef BOOT_RESIDENT
 const char *s="V11 RESIDENT ENTRY - before C runtime";
#else
 const char *s="V11 FRONTEND ENTRY - before C runtime";
#endif
 for(int i=0;s[i];i++)scr_putchar(16+i*8,32,0xffffff,s[i]);
 hold();
}
void checkpoint_hold(void) {hold();}
