cdef extern from "linux/if.h":
    cpdef enum:
        IFF_UP
        IFF_RUNNING
cdef extern from "linux/if_addr.h":
    struct ifaddrmsg:
        unsigned char   ifa_family
        unsigned char   ifa_prefixlen
        unsigned char   ifa_flags
        unsigned char   ifa_scope
        unsigned int    ifa_index
    rtattr* IFA_RTA(ifaddrmsg*)
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
    cdef int NLMSG_ALIGN(int)
    cdef void* NLMSG_DATA(nlmsghdr*)
#    cdef int NLMSG_PAYLOAD(nlmsghdr*, len)
cdef extern from "linux/rtnetlink.h":
    cpdef enum:
        RTMGRP_LINK
        RTM_NEWLINK
        RTM_DELLINK
        RTM_NEWROUTE
        RTM_DELROUTE
    struct ifinfomsg:
# N.B. Cython has trouble with the padding member (because of mangling of
# double underscore) before version 3.0.a3 (commit 25b7d7e4), hence only
# members after the padding are accessible ; stable 3.0 is not released as
# of this writing.
#        unsigned char   ifi_family
#        unsigned char   __ifi_pad
        unsigned short  ifi_type
        int             ifi_index
        unsigned int    ifi_flags
        unsigned int    ifi_change
    struct rtattr:
        unsigned short  rta_len
        unsigned short  rta_type
    cdef int RTA_ALIGN(int)
    cdef bint RTA_OK(rtattr*, int)
    cdef int RTA_LENGTH(int)
    cdef int RTM_PAYLOAD(nlmsghdr*)
    rtattr* RTA_NEXT(rtattr*, int)
#    cdef void* RTA_DATA(rtattr)
cdef extern from "linux/if_link.h":
    cpdef enum:
        IFLA_IFNAME
    cdef rtattr* IFLA_RTA(ifinfomsg*)

#cpdef (unsigned int, unsigned short, unsigned short, unsigned int, unsigned int) get_header(bytes)
#cpdef nlmsghdr get_header(bytes)

# ifinfomsg
cpdef (unsigned short, int, unsigned int, unsigned int) get_ifinfomsg(bytes)

cpdef unsigned int get_ifinfomsg_flags(bytes)

#cpdef (unsigned short, unsigned short) get_rtattr(bytes)
cpdef rtattr get_rtattr(bytes)

cpdef int get_sizeof_header(nlmsghdr)

#cpdef int get_nlmsg_hdrlen()
