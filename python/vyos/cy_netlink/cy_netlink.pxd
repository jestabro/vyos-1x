cdef extern from "linux/if_link.h":
    cpdef enum:
        IFLA_IFNAME
cdef extern from "linux/netlink.h":
    cpdef enum:
        NLMSG_NOOP
        NLMSG_ERROR
        NLMSG_HDRLEN
    cdef struct nlmsghdr:
        unsigned int    nlmsg_len
        unsigned short  nlmsg_type
        unsigned short  nlmsg_flags
        unsigned int    nlmsg_seq
        unsigned int    nlmsg_pid
#    cdef int NLMSG_HDRLEN
    cdef int NLMSG_ALIGN(int)
#    cdef int NLMSG_PAYLOAD(nlmsghdr*, len)
cdef extern from "linux/rtnetlink.h":
    cpdef enum:
        RTMGRP_LINK
        RTM_NEWLINK
        RTM_DELLINK
    cdef struct rtattr:
        unsigned short  rta_len
        unsigned short  rta_type
    cdef int RTA_ALIGN(int)
    cdef bint RTA_OK(rtattr*, int)
    cdef int RTA_LENGTH(int)
    cdef int RTM_PAYLOAD(nlmsghdr*)
    rtattr* RTA_NEXT(rtattr*, int)
#    cdef void* RTA_DATA(rtattr)

#cpdef (unsigned int, unsigned short, unsigned short, unsigned int, unsigned int) get_header(bytes)
cpdef nlmsghdr get_header(bytes)

#cpdef (unsigned short, unsigned short) get_rtattr(bytes)
cpdef rtattr get_rtattr(bytes)

cpdef int get_sizeof_header(nlmsghdr)

#cpdef int get_nlmsg_hdrlen()
