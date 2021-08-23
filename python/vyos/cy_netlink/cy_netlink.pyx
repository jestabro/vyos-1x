
#from cy_netlink cimport RTMGRP_LINK, RTM_NEWLINK, RTM_DELLINK, nlmsghdr
from libc.string cimport memcpy
from cython.operator cimport dereference
#from cpython.ref cimport PyObject
cimport cy_netlink

#cdef extern from *:
#    ctypedef Py_ssize_t Py_intptr_t

#cpdef (unsigned int, unsigned short, unsigned short, unsigned int, unsigned int) get_header(bytes buf):
cpdef nlmsghdr get_header(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef nlmsghdr hdr
    memcpy(&hdr, buf_ptr, sizeof(nlmsghdr))
    return hdr
#    return (hdr.nlmsg_len, hdr.nlmsg_type, hdr.nlmsg_flags, hdr.nlmsg_seq, hdr.nlmsg_pid)

#cpdef (unsigned short, unsigned short) get_rtattr(bytes buf):
cpdef rtattr get_rtattr(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    print(f"JSE buf: {buf}, buf_view: {buf_view}")
    cdef char* buf_ptr = <char*>&buf_view[0]
#    cdef rtattr attr = dereference(<rtattr*>buf_ptr)
    cdef rtattr attr
    memcpy(&attr, buf_ptr, sizeof(rtattr))
    return attr
#    return (attr.rta_len, attr.rta_type)

cpdef int rtm_payload(nlmsghdr nlh):
    return RTM_PAYLOAD(&nlh)

cpdef int rta_align(int len):
    return RTA_ALIGN(len)

cpdef bint rta_ok(rtattr attr, int alen):
    return RTA_OK(&attr, alen)

ctypedef void* void_star

cpdef bytes rta_data(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef bytes data = <bytes>(buf_ptr + RTA_LENGTH(0))
    return data

#cpdef object py_rta_data(rtattr):
#    cdef bytes data_ptr = <bytes>RTA_DATA(rtattr)
#    cdef PyObject *data_ptr = <PyObject*>(RTA_DATA(rtattr))
#    cdef Py_intptr_t address = <Py_intptr_t>data_ptr
#    return <object>data_ptr

#print(f"type of RTA_DATA: {type(RTA_DATA)}")
print(f"RTA_ALIGN(0): {RTA_ALIGN(0)}")
print(f"RTA_LENGTH(0): {RTA_LENGTH(0)}")
print(f"RTMGRP_LINK: {RTMGRP_LINK}")
print(f"NLMSG_NOOP: {NLMSG_NOOP}")
print(f"NLMSG_ERROR: {NLMSG_ERROR}")
print(f"RTM_NEWLINK: {RTM_NEWLINK}")
print(f"RTM_DELLINK: {RTM_DELLINK}")
print(f"IFLA_IFNAME: {IFLA_IFNAME}")
print(f"NLMSG_HDRLEN: {NLMSG_HDRLEN}")
