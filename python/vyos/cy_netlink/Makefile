.PHONY: cython_build
cython_build:
	./cythonize -3 -i --lenient cy_netlink.pyx

.PHONY: clean
clean:
	rm -rf build/
	rm -f cy_netlink.cpython-39-x86_64-linux-gnu.so
	rm -f cy_netlink.c

