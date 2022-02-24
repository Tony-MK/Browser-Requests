	.file	"main.c"
	.comm	_fileptr, 4, 2
	.globl	_FILE_NAME
	.section .rdata,"dr"
	.align 4
LC0:
	.ascii "C:/Users/Tony/Desktop/Personal/Projects/browser_requests/logs/network_log.json\0"
	.data
	.align 4
_FILE_NAME:
	.long	LC0
	.section .rdata,"dr"
LC1:
	.ascii "%d\12\0"
	.text
	.globl	_print_stats
	.def	_print_stats;	.scl	2;	.type	32;	.endef
_print_stats:
LFB14:
	.cfi_startproc
	pushl	%ebp
	.cfi_def_cfa_offset 8
	.cfi_offset 5, -8
	movl	%esp, %ebp
	.cfi_def_cfa_register 5
	subl	$24, %esp
	movl	_fileptr, %eax
	movl	%eax, (%esp)
	call	_ftell
	movl	%eax, 4(%esp)
	movl	$LC1, (%esp)
	call	_printf
	nop
	leave
	.cfi_restore 5
	.cfi_def_cfa 4, 4
	ret
	.cfi_endproc
LFE14:
	.def	___main;	.scl	2;	.type	32;	.endef
	.section .rdata,"dr"
LC2:
	.ascii "r\0"
LC3:
	.ascii "FILE NOT FOUND\0"
LC4:
	.ascii "Opening File : %s\0"
LC5:
	.ascii "%[^\12]%*c\0"
	.align 4
LC6:
	.ascii "\12File Length: %d\12Closing File...\0"
	.text
	.globl	_main
	.def	_main;	.scl	2;	.type	32;	.endef
_main:
LFB15:
	.cfi_startproc
	pushl	%ebp
	.cfi_def_cfa_offset 8
	.cfi_offset 5, -8
	movl	%esp, %ebp
	.cfi_def_cfa_register 5
	andl	$-16, %esp
	subl	$32, %esp
	call	___main
	movl	_FILE_NAME, %eax
	movl	$LC2, 4(%esp)
	movl	%eax, (%esp)
	call	_fopen
	movl	%eax, _fileptr
	movl	_fileptr, %eax
	testl	%eax, %eax
	jne	L3
	movl	$LC3, (%esp)
	call	_puts
	movl	$1, (%esp)
	call	_exit
L3:
	movl	_FILE_NAME, %eax
	movl	%eax, 4(%esp)
	movl	$LC4, (%esp)
	call	_printf
	movl	_fileptr, %eax
	movl	$1, 8(%esp)
	movl	$16777216, 4(%esp)
	movl	%eax, (%esp)
	call	_fseek
	movb	$0, 31(%esp)
L4:
	movl	$100000000, (%esp)
	call	_malloc
	movl	%eax, 24(%esp)
	movl	_fileptr, %eax
	movl	24(%esp), %edx
	movl	%edx, 8(%esp)
	movl	$LC5, 4(%esp)
	movl	%eax, (%esp)
	call	_fscanf
	movl	%eax, 4(%esp)
	movl	$LC1, (%esp)
	call	_printf
	movl	24(%esp), %eax
	movl	%eax, (%esp)
	call	_free
	cmpb	$16, 31(%esp)
	jne	L4
	movl	_fileptr, %eax
	movl	%eax, (%esp)
	call	_ftell
	movl	%eax, 4(%esp)
	movl	$LC6, (%esp)
	call	_printf
	movl	_fileptr, %eax
	movl	%eax, (%esp)
	call	_fclose
	movl	$0, %eax
	leave
	.cfi_restore 5
	.cfi_def_cfa 4, 4
	ret
	.cfi_endproc
LFE15:
	.ident	"GCC: (MinGW.org GCC-6.3.0-1) 6.3.0"
	.def	_ftell;	.scl	2;	.type	32;	.endef
	.def	_printf;	.scl	2;	.type	32;	.endef
	.def	_fopen;	.scl	2;	.type	32;	.endef
	.def	_puts;	.scl	2;	.type	32;	.endef
	.def	_exit;	.scl	2;	.type	32;	.endef
	.def	_fseek;	.scl	2;	.type	32;	.endef
	.def	_malloc;	.scl	2;	.type	32;	.endef
	.def	_fscanf;	.scl	2;	.type	32;	.endef
	.def	_free;	.scl	2;	.type	32;	.endef
	.def	_fclose;	.scl	2;	.type	32;	.endef
