SERVICE_FILES = $(wildcard *.service)
TARGET_FILES = $(addprefix snippets/,${SERVICE_FILES})

ifeq ($(USER),)
USER=$(shell whoami)
endif
ifeq ($(WORKDIR),)
WORKDIR=$(CURDIR)
endif

all: ${TARGET_FILES}

snippets/%.service: %.service
	sed "s|<user>|${USER}|" $< | sed "s|<workdir>|${WORKDIR}|" > $@

install: ${TARGET_FILES}
	sh snippets/install.sh ${INSTALL}

show:
	#echo $${USER:-$$(whoami)} $${WORKDIR:-$$(pwd)}
	echo ${USER} ${WORKDIR}

clean:
	rm -f ${TARGET_FILES}
