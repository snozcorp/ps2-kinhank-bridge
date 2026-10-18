.text
.set noreorder
.globl checked_entry
.ent checked_entry
checked_entry:
 la $gp,_gp
 la $sp,entry_stack+8192
 jal early_screen
 nop
 j __start
 move $a0,$zero
.end checked_entry
