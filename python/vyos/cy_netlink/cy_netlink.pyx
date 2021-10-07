
#from cy_netlink cimport RTMGRP_LINK, RTM_NEWLINK, RTM_DELLINK, nlmsghdr
from libc.string cimport memcpy, memset
from cython.operator cimport dereference
#from cpython.ref cimport PyObject
cimport cy_netlink

cpdef nlmsghdr get_header(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef nlmsghdr hdr = dereference(<nlmsghdr*>buf_ptr)
#    memcpy(&hdr, buf_ptr, sizeof(nlmsghdr))
    return hdr
#    return (hdr.nlmsg_len, hdr.nlmsg_type, hdr.nlmsg_flags, hdr.nlmsg_seq, hdr.nlmsg_pid)

cpdef bytes Nlmsg_Data(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    buf_ptr = <char*>NLMSG_DATA(<nlmsghdr*>buf_ptr)
    return <bytes>buf_ptr

cpdef bytes ifla_rta(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef char* ret_ptr = <char*>IFLA_RTA(<ifinfomsg*>buf_ptr)
    return <bytes>ret_ptr

cpdef bytes ifa_rta(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    buf_ptr = <char*>IFA_RTA(<ifaddrmsg*>buf_ptr)
    return <bytes>buf_ptr

cpdef int get_sizeof_header(nlmsghdr h):
    return sizeof(h)

cpdef (unsigned char, unsigned short, int, unsigned int, unsigned int) get_ifinfomsg(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef ifinfomsg ifi = dereference(<ifinfomsg*>buf_ptr)
    return (ifi.ifi_family, ifi.ifi_type, ifi.ifi_index, ifi.ifi_flags, ifi.ifi_change)

#cpdef ifinfomsg get_ifinfomsg(nlmsghdr h):
#    cdef nlmsghdr* h_ptr = <nlmsghdr*>&h
#    cdef ifinfomsg* info = <ifinfomsg*>NLMSG_DATA(h_ptr)
#    return dereference(info)

cpdef object test_return():
    cdef rtattr tb[24];
    memset(&tb, 0, sizeof(rtattr) * 24);
    return tb

cpdef rtattr get_rtattr(bytes buf):
    cdef const unsigned char[:] buf_view = buf
#    print(f"JSE buf: {buf}, buf_view: {buf_view}")
    cdef char* buf_ptr = <char*>&buf_view[0]
#    cdef rtattr attr = dereference(<rtattr*>buf_ptr)
    cdef rtattr attr;
    memcpy(&attr, buf_ptr, sizeof(rtattr))
    return attr
#    return (attr.rta_len, attr.rta_type)

cpdef int rtm_payload(nlmsghdr nlh):
    return RTM_PAYLOAD(&nlh)

cpdef int rta_align(int leng):
    return RTA_ALIGN(leng)

cpdef int nlmsg_align(int leng):
    return NLMSG_ALIGN(leng)

cpdef bint rta_ok(rtattr attr, int alen):
    return RTA_OK(&attr, alen)

ctypedef void* void_star

cpdef bytes rta_data(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef bytes data = <bytes>(buf_ptr + RTA_LENGTH(0))
    return data

#cdef pre_rta_next(rtattr *attr, int *attr_len):
#    cdef rtattr* ret = RTA_NEXT(attr, dereference(attr_len))
#    return ret

cpdef rtattr rta_next(rtattr rta, int leng):
    return dereference(RTA_NEXT(&rta, leng))

cpdef bytes prev_rta_next(bytes buf, list len_list):
    cdef const unsigned char[:] buf_view = buf
    cdef rtattr* attr = <rtattr*>&buf_view[0]
    cdef int attrlen = len_list[0]
    print(f"JSE 1 attrlen: {attrlen}")
#    cdef rtattr* ret = pre_rta_next(attr, &attrlen)
    cdef char* ret = <char*>RTA_NEXT(attr, attrlen)
    print(f"JSE 2 attrlen: {attrlen}")
    len_list[0] = attrlen
    cdef bytes data = <bytes>ret
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
