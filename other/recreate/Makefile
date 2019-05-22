
objects := $(patsubst %.c,%.o,$(wildcard *.c))

all : $(objects)
	gcc -o recreate $(objects) -lm

clean:
	rm *o recreate
