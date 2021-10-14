.PHONY: cython_build
cython_build:
	./cythonize -3 -i netlink.pyx

.PHONY: clean
clean:
	rm -rf build/
	rm -f netlink.cpython-39-x86_64-linux-gnu.so
	rm -f netlink.c

