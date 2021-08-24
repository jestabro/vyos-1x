cdef extern from "linux/if_link.h":
    cpdef enum:
        IFLA_IFNAME
cdef extern from "linux/netlink.h":
    cpdef enum:
        NLMSG_NOOP
        NLMSG_ERROR
    cdef int NLMSG_HDRLEN
cdef extern from "linux/rtnetlink.h":
    cpdef enum:
        RTMGRP_LINK
        RTM_NEWLINK
        RTM_DELLINK
    cdef struct nlmsghdr:
        unsigned int    nlmsg_len
        unsigned short  nlmsg_type
        unsigned short  nlmsg_flags
        unsigned int    nlmsg_seq
        unsigned int    nlmsg_pid
    cdef struct rtattr:
        unsigned short  rta_len
        unsigned short  rta_type
    cdef bint RTA_OK(rtattr, int)
    cdef int RTA_LENGTH(int)
#    cdef void* RTA_DATA(rtattr)

cpdef (unsigned int, unsigned short, unsigned short, unsigned int, unsigned int) get_header(bytes)

cpdef (unsigned short, unsigned short) get_rtattr(bytes)
