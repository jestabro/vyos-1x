# Copyright 2022 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

cdef extern from "linux/if.h":
    cpdef enum:
        IFF_UP
        IFF_RUNNING
cdef extern from "linux/if_addr.h":
    cpdef enum:
        IFA_LOCAL
        IFA_MAX
    struct ifaddrmsg:
        unsigned char   ifa_family
        unsigned char   ifa_prefixlen
        unsigned char   ifa_flags
        unsigned char   ifa_scope
        unsigned int    ifa_index
    rtattr* IFA_RTA(ifaddrmsg*)
cdef extern from "linux/if_link.h":
    cpdef enum:
        IFLA_IFNAME
        IFLA_MAX
    rtattr* IFLA_RTA(ifinfomsg*)
cdef extern from "linux/netlink.h":
    cpdef enum:
        NLMSG_NOOP
        NLMSG_ERROR
        NLMSG_HDRLEN
    struct nlmsghdr:
        unsigned int    nlmsg_len
        unsigned short  nlmsg_type
        unsigned short  nlmsg_flags
        unsigned int    nlmsg_seq
        unsigned int    nlmsg_pid
    int NLMSG_ALIGN(int)
    void* NLMSG_DATA(nlmsghdr*)
cdef extern from "linux/rtnetlink.h":
    cpdef enum:
        RTMGRP_LINK
        RTMGRP_IPV4_IFADDR
        RTM_NEWLINK
        RTM_DELLINK
        RTM_NEWADDR
        RTM_DELADDR
    struct ifinfomsg:
# N.B.: Cython has trouble with the padding member (because of mangling of
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
    int  RTA_ALIGN(int)
    bint RTA_OK(rtattr*, int)
    int  RTA_LENGTH(int)
