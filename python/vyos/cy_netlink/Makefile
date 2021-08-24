.PHONY: cython_build
cython_build:
	./cythonize -3 -i cy_netlink.pyx
	touch was_here

.PHONY: clean
clean:
	rm -rf build/
	rm -f cy_netlink.cpython-39-x86_64-linux-gnu.so
	rm -f cy_netlink.c
	rm -f was_here

