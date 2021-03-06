include $(MSCDIR)/software/include/generated/cpu.mak
TARGET_PREFIX=$(CPU)-elf-

RM ?= rm -f

CC_normal := $(TARGET_PREFIX)gcc
CX_normal := $(TARGET_PREFIX)g++
AS_normal := $(TARGET_PREFIX)as
AR_normal := $(TARGET_PREFIX)ar
LD_normal := $(TARGET_PREFIX)ld
OBJCOPY_normal := $(TARGET_PREFIX)objcopy
RANLIB_normal := $(TARGET_PREFIX)ranlib

CC_quiet = @echo " CC      " $@ && $(TARGET_PREFIX)gcc
CX_quiet = @echo " CX      " $@ && $(TARGET_PREFIX)g++
AS_quiet = @echo " AS      " $@ && $(TARGET_PREFIX)as
AR_quiet = @echo " AR      " $@ && $(TARGET_PREFIX)ar
LD_quiet = @echo " LD      " $@ && $(TARGET_PREFIX)ld
OBJCOPY_quiet = @echo " OBJCOPY " $@ && $(TARGET_PREFIX)objcopy
RANLIB_quiet = @echo " RANLIB   " $@ && $(TARGET_PREFIX)ranlib

MSC_GIT_ID := $(shell cd $(MSCDIR) && python3 -c "from misoclib.cpu.identifier import get_id; print(hex(get_id()), end='')")

ifeq ($(V),1)
	CC = $(CC_normal)
	CX = $(CX_normal)
	AS = $(AS_normal)
	AR = $(AR_normal)
	LD = $(LD_normal)
	OBJCOPY = $(OBJCOPY_normal)
	RANLIB = $(RANLIB_normal)
else
	CC = $(CC_quiet)
	CX = $(CX_quiet)
	AS = $(AS_quiet)
	AR = $(AR_quiet)
	LD = $(LD_quiet)
	OBJCOPY = $(OBJCOPY_quiet)
	RANLIB = $(RANLIB_quiet)
endif

# Toolchain options
#
INCLUDES = -I$(MSCDIR)/software/include/base -I$(MSCDIR)/software/include -I$(MSCDIR)/common
COMMONFLAGS = -Os $(CPUFLAGS) -Wall -fno-builtin -nostdinc -DMSC_GIT_ID=$(MSC_GIT_ID) $(INCLUDES)
CFLAGS = $(COMMONFLAGS) -Wstrict-prototypes -Wold-style-definition -Wmissing-prototypes
CXXFLAGS = $(COMMONFLAGS) -fno-exceptions -ffreestanding
LDFLAGS = -nostdlib -nodefaultlibs -L$(MSCDIR)/software/include

# compile and generate dependencies, based on
# http://scottmcpeak.com/autodepend/autodepend.html

define compilexx-dep
$(CX) -c $(CXXFLAGS) $(1) $< -o $*.o
@$(CX_normal) -MM $(CXXFLAGS) $(1) $< > $*.d
@mv -f $*.d $*.d.tmp
@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
@rm -f $*.d.tmp
endef

define compile-dep
$(CC) -c $(CFLAGS) $(1) $< -o $*.o
@$(CC_normal) -MM $(CFLAGS) $(1) $< > $*.d
@mv -f $*.d $*.d.tmp
@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
@rm -f $*.d.tmp
endef

define assemble
$(CC) -c $(CFLAGS) -o $*.o $<
endef
