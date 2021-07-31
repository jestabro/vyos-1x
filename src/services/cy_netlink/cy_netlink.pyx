
#from cy_netlink cimport RTMGRP_LINK, RTM_NEWLINK, RTM_DELLINK, nlmsghdr
from libc.string cimport memcpy
cimport cy_netlink

cpdef (unsigned int, unsigned short, unsigned short, unsigned int, unsigned int) get_header(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef nlmsghdr hdr
    memcpy(&hdr, buf_ptr, sizeof(nlmsghdr))
    return (hdr.nlmsg_len, hdr.nlmsg_type, hdr.nlmsg_flags, hdr.nlmsg_seq, hdr.nlmsg_pid)
#    return (nlmsg_len, nlmsg_type, nlmsg_flags, nlmsg_seq, nlmsg_pid)

cpdef (unsigned short, unsigned short) get_rtattr(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef rtattr attr
    memcpy(&attr, buf_ptr, sizeof(rtattr))
    return (attr.rta_len, attr.rta_type)

#cdef extern from "linux/rtnetlink.h":
#    bint RTA_OK(rtattr, int)

#RTMGRP_LINK=cy_netlink.RTMGRP_LINK

#print("Hello World")
print(f"RTMGRP_LINK: {RTMGRP_LINK}")
print(f"NLMSG_NOOP: {NLMSG_NOOP}")
print(f"NLMSG_ERROR: {NLMSG_ERROR}")
print(f"RTM_NEWLINK: {RTM_NEWLINK}")
print(f"RTM_DELLINK: {RTM_DELLINK}")
print(f"IFLA_IFNAME: {IFLA_IFNAME}")
