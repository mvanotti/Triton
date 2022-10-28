#!/usr/bin/env python3
## -*- coding: utf-8 -*-

from __future__          import print_function

from triton              import *
from unicorn             import *
from unicorn.arm64_const import *
from struct              import pack

import sys
import pprint

ADDR  = 0x100000
STACK = 0x200000
HEAP  = 0x300000
SIZE  = 5 * 1024 * 1024

CODE  = [
    (b"\x08\x08\x00\x90", "adrp x8, #0x100000"),
    (b"\x08\x59\x00\x91", "add x8, x8, #0x16"),
    (b"\x2b\x00\x80\xd2", "mov x11, 1"),
    (b"\x0a\x79\xab\xb8", "ldrsw x10, [x8, x11, lsl #2]"),
    (b"\x09\x01\x0a\x8b", "add x9, x8, x10"),

    (b"\x41\x24\x82\xd2", "mov x1, 0x1122"),
    (b"\x42\xf5\x8e\xd2", "mov x2, 0x77aa"),
    (b"\x63\x40\x99\xd2", "mov x3, 0xca03"),
    (b"\x21\x7c\x02\x9b", "mul x1, x1, x2"),
    (b"\x21\x7c\x02\x9b", "mul x1, x1, x2"),
    (b"\x21\x7c\x02\x9b", "mul x1, x1, x2"),
    (b"\x43\x7c\x03\x9b", "mul x3, x2, x3"),
    (b"\x43\x7c\x03\x9b", "mul x3, x2, x3"),
    (b"\x41\x04\x41\xb3", "bfxil x1, x2, #1, #1"),
    (b"\x41\x08\x41\xb3", "bfxil x1, x2, #1, #2"),
    (b"\x41\x0c\x41\xb3", "bfxil x1, x2, #1, #3"),
    (b"\x41\x10\x41\xb3", "bfxil x1, x2, #1, #4"),
    (b"\x41\x14\x41\xb3", "bfxil x1, x2, #1, #5"),
    (b"\x41\x18\x41\xb3", "bfxil x1, x2, #1, #6"),
    (b"\x41\x1c\x41\xb3", "bfxil x1, x2, #1, #7"),
    (b"\x41\x7c\x41\xb3", "bfxil x1, x2, #1, #31"),
    (b"\x41\x04\x41\xb3", "bfxil x1, x2, #1, #1"),
    (b"\x41\x0c\x42\xb3", "bfxil x1, x2, #2, #2"),
    (b"\x41\x14\x43\xb3", "bfxil x1, x2, #3, #3"),
    (b"\x41\x1c\x44\xb3", "bfxil x1, x2, #4, #4"),
    (b"\x41\x24\x45\xb3", "bfxil x1, x2, #5, #5"),
    (b"\x41\x2c\x46\xb3", "bfxil x1, x2, #6, #6"),
    (b"\x41\x34\x47\xb3", "bfxil x1, x2, #7, #7"),
    (b"\x41\x98\x48\xb3", "bfxil x1, x2, #8, #31"),

    (b"\x80\x46\x82\xd2", "movz x0, #0x1234"),
    (b"\x80\x46\xa2\xd2", "movz x0, #0x1234, lsl #16"),
    (b"\x80\x46\xc2\xd2", "movz x0, #0x1234, lsl #32"),
    (b"\x80\x46\xe2\xd2", "movz x0, #0x1234, lsl #48"),
    (b"\x21\x64\x88\xd2", "movz x1, #0x4321"),
    (b"\x21\x64\xa8\xd2", "movz x1, #0x4321, lsl #16"),
    (b"\x21\x64\xc8\xd2", "movz x1, #0x4321, lsl #32"),
    (b"\x21\x64\xe8\xd2", "movz x1, #0x4321, lsl #48"),
    (b"\x21\x64\xe8\xd2", "movz x1, #0x4321, lsl #48"),
    (b"\x21\x64\xc8\xd2", "movz x1, #0x4321, lsl #32"),
    (b"\x21\x64\xa8\xd2", "movz x1, #0x4321, lsl #16"),

    (b"\x21\x64\x88\xf2", "movk x1, #0x4321"),
    (b"\x81\x46\xa2\xf2", "movk x1, #0x1234, lsl #16"),
    (b"\x81\x04\xcf\xf2", "movk x1, #0x7824, lsl #32"),
    (b"\x61\x8a\xf2\xf2", "movk x1, #0x9453, lsl #48"),

    (b"\xe0\xcc\x8c\x52", "movz w0, #0x6667"),
    (b"\xc0\xcc\xac\x72", "movk w0, #0x6666, lsl #16"),

    (b"\x1f\x20\x03\xd5", "nop"),
    (b"\x1f\x20\x03\xd5", "nop"),
    (b"\x1f\x20\x03\xd5", "nop"),

    (b"\x60\x00\x02\x8b", "add x0, x3, x2"),
    (b"\x20\x00\x02\x8b", "add x0, x1, x2"),
    (b"\x80\x46\xa2\xd2", "movz x0, #0x1234, lsl #16"),
    (b"\x00\x00\x00\x8b", "add x0, x0, x0"),
    (b"\x60\xc0\x22\x8b", "add x0, x3, w2, sxtw"),
    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x80\x22\x8b", "add x0, x1, w2, sxtb"),
    (b"\x20\xa0\x22\x8b", "add x0, x1, w2, sxth"),
    (b"\x20\xc0\x22\x8b", "add x0, x1, w2, sxtw"),
    (b"\x20\xe0\x22\x8b", "add x0, x1, x2, sxtx"),
    (b"\x20\x00\x02\x8b", "add x0, x1, x2, lsl #0"),
    (b"\x20\x04\x02\x8b", "add x0, x1, x2, lsl #1"),
    (b"\x20\x20\x02\x8b", "add x0, x1, x2, lsl #8"),
    (b"\x20\x40\x02\x8b", "add x0, x1, x2, lsl #16"),
    (b"\x20\x80\x02\x8b", "add x0, x1, x2, lsl #32"),
    (b"\x20\x84\x02\x8b", "add x0, x1, x2, lsl #33"),
    (b"\x20\x88\x02\x8b", "add x0, x1, x2, lsl #34"),
    (b"\x20\x00\x42\x8b", "add x0, x1, x2, lsr #0"),
    (b"\x20\x04\x42\x8b", "add x0, x1, x2, lsr #1"),
    (b"\x20\x20\x42\x8b", "add x0, x1, x2, lsr #8"),
    (b"\x20\x40\x42\x8b", "add x0, x1, x2, lsr #16"),
    (b"\x20\x80\x42\x8b", "add x0, x1, x2, lsr #32"),
    (b"\x20\x84\x42\x8b", "add x0, x1, x2, lsr #33"),
    (b"\x20\x88\x42\x8b", "add x0, x1, x2, lsr #34"),
    (b"\x20\x20\x82\x8b", "add x0, x1, x2, asr #8"),
    (b"\x20\x40\x82\x8b", "add x0, x1, x2, asr #16"),
    (b"\x20\x80\x82\x8b", "add x0, x1, x2, asr #32"),
    (b"\x20\x84\x82\x8b", "add x0, x1, x2, asr #33"),
    (b"\x20\x88\x82\x8b", "add x0, x1, x2, asr #34"),
    (b"\x20\x88\x82\x8b", "add x0, x1, x2, asr #34"),
    (b"\x20\x88\x19\x91", "add x0, x1, #1634"),
    (b"\x20\x58\x21\x91", "add x0, x1, #2134"),
    (b"\x20\x58\x61\x91", "add x0, x1, #2134, lsl #12"),
    (b"\x3f\x60\x22\x8b", "add sp, x1, x2"),

    (b"\x60\x00\x02\xab", "adds x0, x3, x2"),
    (b"\x20\x00\x02\xab", "adds x0, x1, x2"),
    (b"\x80\x46\xa2\xd2", "movz x0, #0x1234, lsl #16"),
    (b"\x00\x00\x00\xab", "adds x0, x0, x0"),
    (b"\x60\xc0\x22\xab", "adds x0, x3, w2, sxtw"),
    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x80\x22\xab", "adds x0, x1, w2, sxtb"),
    (b"\x20\xa0\x22\xab", "adds x0, x1, w2, sxth"),
    (b"\x20\xc0\x22\xab", "adds x0, x1, w2, sxtw"),
    (b"\x20\xe0\x22\xab", "adds x0, x1, x2, sxtx"),
    (b"\x20\x00\x02\xab", "adds x0, x1, x2, lsl #0"),
    (b"\x20\x04\x02\xab", "adds x0, x1, x2, lsl #1"),
    (b"\x20\x20\x02\xab", "adds x0, x1, x2, lsl #8"),
    (b"\x20\x40\x02\xab", "adds x0, x1, x2, lsl #16"),
    (b"\x20\x80\x02\xab", "adds x0, x1, x2, lsl #32"),
    (b"\x20\x84\x02\xab", "adds x0, x1, x2, lsl #33"),
    (b"\x20\x88\x02\xab", "adds x0, x1, x2, lsl #34"),
    (b"\x20\x00\x42\xab", "adds x0, x1, x2, lsr #0"),
    (b"\x20\x04\x42\xab", "adds x0, x1, x2, lsr #1"),
    (b"\x20\x20\x42\xab", "adds x0, x1, x2, lsr #8"),
    (b"\x20\x40\x42\xab", "adds x0, x1, x2, lsr #16"),
    (b"\x20\x80\x42\xab", "adds x0, x1, x2, lsr #32"),
    (b"\x20\x84\x42\xab", "adds x0, x1, x2, lsr #33"),
    (b"\x20\x88\x42\xab", "adds x0, x1, x2, lsr #34"),
    (b"\x20\x20\x82\xab", "adds x0, x1, x2, asr #8"),
    (b"\x20\x40\x82\xab", "adds x0, x1, x2, asr #16"),
    (b"\x20\x80\x82\xab", "adds x0, x1, x2, asr #32"),
    (b"\x20\x84\x82\xab", "adds x0, x1, x2, asr #33"),
    (b"\x20\x88\x82\xab", "adds x0, x1, x2, asr #34"),
    (b"\x20\x88\x82\xab", "adds x0, x1, x2, asr #34"),
    (b"\x20\x88\x19\xb1", "adds x0, x1, #1634"),
    (b"\x20\x58\x21\xb1", "adds x0, x1, #2134"),
    (b"\x20\x58\x61\xb1", "adds x0, x1, #2134, lsl #12"),
    (b"\x00\x00\x00\xab", "adds x0, x0, x0"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x00\x04\x00\xb1", "adds x0, x0, #1"),

    (b"\x20\x00\x02\x9a", "adc x0, x1, x2"),
    (b"\x20\x00\x02\x1a", "adc w0, w1, w2"),

    (b"\x20\x1a\x09\x30", "adr x0, #0x12345"),
    (b"\xe1\xff\x7f\x70", "adr x1, #0xfffff"),

    (b"\xc1\x7c\x00\xd0", "adrp x1, #0xf9a000"),
    (b"\x41\x0c\x00\xf0", "adrp x1, #0x18b000"),

    (b"\xe1\xff\x9f\xd2", "movz x1, #0xffff"),
    (b"\x22\x00\x80\xd2", "movz x2, #0x1"),
    (b"\x20\x1c\x40\x92", "and x0, x1, #0xff"),
    (b"\x20\x00\x40\x92", "and x0, x1, #0x01"),
    (b"\x20\x00\x7c\x92", "and x0, x1, #0x10"),
    (b"\x20\x00\x02\x8a", "and x0, x1, x2"),
    (b"\x20\x04\x02\x8a", "and x0, x1, x2, lsl #1"),
    (b"\x20\x08\x02\x8a", "and x0, x1, x2, lsl #2"),
    (b"\x20\x0c\x02\x8a", "and x0, x1, x2, lsl #3"),
    (b"\x20\x10\x02\x8a", "and x0, x1, x2, lsl #4"),
    (b"\x20\x1c\x40\xf2", "ands x0, x1, #0xff"),
    (b"\x20\x00\x40\xf2", "ands x0, x1, #0x01"),
    (b"\x20\x00\x7c\xf2", "ands x0, x1, #0x10"),
    (b"\x20\x00\x02\xea", "ands x0, x1, x2"),
    (b"\x20\x04\x02\xea", "ands x0, x1, x2, lsl #1"),
    (b"\x20\x08\x02\xea", "ands x0, x1, x2, lsl #2"),
    (b"\x20\x0c\x02\xea", "ands x0, x1, x2, lsl #3"),
    (b"\x20\x10\x02\xea", "ands x0, x1, x2, lsl #4"),
    (b"\x3f\x1c\x40\xf2", "tst x1, #0xff"),
    (b"\x3f\x00\x40\xf2", "tst x1, #0x01"),
    (b"\x3f\x00\x7c\xf2", "tst x1, #0x10"),
    (b"\x3f\x00\x02\xea", "tst x1, x2"),
    (b"\x3f\x04\x02\xea", "tst x1, x2, lsl #1"),
    (b"\x3f\x08\x02\xea", "tst x1, x2, lsl #2"),
    (b"\x3f\x0c\x02\xea", "tst x1, x2, lsl #3"),
    (b"\x3f\x10\x02\xea", "tst x1, x2, lsl #4"),

    (b"\x20\xfc\x41\x93", "asr x0, x1, #1"),
    (b"\x20\xfc\x42\x93", "asr x0, x1, #2"),
    (b"\x20\xfc\x43\x93", "asr x0, x1, #3"),
    (b"\x20\xfc\x44\x93", "asr x0, x1, #4"),
    (b"\x20\xfc\x44\x93", "asr x0, x1, #4"),
    (b"\x20\xfc\x7f\x93", "asr x0, x1, #63"),
    (b"\xe1\xff\x9f\xd2", "movz x1, #0xffff"),
    (b"\x22\x00\x80\xd2", "movz x2, #0x1"),
    (b"\x20\x28\xc2\x9a", "asr x0, x1, x2"),
    (b"\x42\x00\x80\xd2", "movz x2, #0x2"),
    (b"\x20\x28\xc2\x9a", "asr x0, x1, x2"),

    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x80\x22\xcb", "sub x0, x1, w2, sxtb"),
    (b"\x20\xa0\x22\xcb", "sub x0, x1, w2, sxth"),
    (b"\x20\xc0\x22\xcb", "sub x0, x1, w2, sxtw"),
    (b"\x20\xe0\x22\xcb", "sub x0, x1, x2, sxtx"),
    (b"\x20\x00\x02\xcb", "sub x0, x1, x2, lsl #0"),
    (b"\x20\x04\x02\xcb", "sub x0, x1, x2, lsl #1"),
    (b"\x20\x20\x02\xcb", "sub x0, x1, x2, lsl #8"),
    (b"\x20\x40\x02\xcb", "sub x0, x1, x2, lsl #16"),
    (b"\x20\x80\x02\xcb", "sub x0, x1, x2, lsl #32"),
    (b"\x20\x84\x02\xcb", "sub x0, x1, x2, lsl #33"),
    (b"\x20\x88\x02\xcb", "sub x0, x1, x2, lsl #34"),
    (b"\x20\x00\x42\xcb", "sub x0, x1, x2, lsr #0"),
    (b"\x20\x04\x42\xcb", "sub x0, x1, x2, lsr #1"),
    (b"\x20\x20\x42\xcb", "sub x0, x1, x2, lsr #8"),
    (b"\x20\x40\x42\xcb", "sub x0, x1, x2, lsr #16"),
    (b"\x20\x80\x42\xcb", "sub x0, x1, x2, lsr #32"),
    (b"\x20\x84\x42\xcb", "sub x0, x1, x2, lsr #33"),
    (b"\x20\x88\x42\xcb", "sub x0, x1, x2, lsr #34"),
    (b"\x20\x20\x82\xcb", "sub x0, x1, x2, asr #8"),
    (b"\x20\x40\x82\xcb", "sub x0, x1, x2, asr #16"),
    (b"\x20\x80\x82\xcb", "sub x0, x1, x2, asr #32"),
    (b"\x20\x84\x82\xcb", "sub x0, x1, x2, asr #33"),
    (b"\x20\x88\x82\xcb", "sub x0, x1, x2, asr #34"),
    (b"\x20\x88\x82\xcb", "sub x0, x1, x2, asr #34"),
    (b"\x20\x88\x19\xd1", "sub x0, x1, #1634"),
    (b"\x20\x58\x21\xd1", "sub x0, x1, #2134"),
    (b"\x20\x58\x61\xd1", "sub x0, x1, #2134, lsl #12"),

    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x80\x22\xeb", "subs x0, x1, w2, sxtb"),
    (b"\x20\xa0\x22\xeb", "subs x0, x1, w2, sxth"),
    (b"\x20\xc0\x22\xeb", "subs x0, x1, w2, sxtw"),
    (b"\x20\xe0\x22\xeb", "subs x0, x1, x2, sxtx"),
    (b"\x20\x00\x02\xeb", "subs x0, x1, x2, lsl #0"),
    (b"\x20\x04\x02\xeb", "subs x0, x1, x2, lsl #1"),
    (b"\x20\x20\x02\xeb", "subs x0, x1, x2, lsl #8"),
    (b"\x20\x40\x02\xeb", "subs x0, x1, x2, lsl #16"),
    (b"\x20\x80\x02\xeb", "subs x0, x1, x2, lsl #32"),
    (b"\x20\x84\x02\xeb", "subs x0, x1, x2, lsl #33"),
    (b"\x20\x88\x02\xeb", "subs x0, x1, x2, lsl #34"),
    (b"\x20\x00\x42\xeb", "subs x0, x1, x2, lsr #0"),
    (b"\x20\x04\x42\xeb", "subs x0, x1, x2, lsr #1"),
    (b"\x20\x20\x42\xeb", "subs x0, x1, x2, lsr #8"),
    (b"\x20\x40\x42\xeb", "subs x0, x1, x2, lsr #16"),
    (b"\x20\x80\x42\xeb", "subs x0, x1, x2, lsr #32"),
    (b"\x20\x84\x42\xeb", "subs x0, x1, x2, lsr #33"),
    (b"\x20\x88\x42\xeb", "subs x0, x1, x2, lsr #34"),
    (b"\x20\x20\x82\xeb", "subs x0, x1, x2, asr #8"),
    (b"\x20\x40\x82\xeb", "subs x0, x1, x2, asr #16"),
    (b"\x20\x80\x82\xeb", "subs x0, x1, x2, asr #32"),
    (b"\x20\x84\x82\xeb", "subs x0, x1, x2, asr #33"),
    (b"\x20\x88\x82\xeb", "subs x0, x1, x2, asr #34"),
    (b"\x20\x88\x82\xeb", "subs x0, x1, x2, asr #34"),
    (b"\x20\x88\x19\xf1", "subs x0, x1, #1634"),
    (b"\x20\x58\x21\xf1", "subs x0, x1, #2134"),
    (b"\x20\x58\x61\xf1", "subs x0, x1, #2134, lsl #12"),

    (b"\x20\x00\x02\xca", "eor x0, x1, x2, lsl #0"),
    (b"\x20\x04\x02\xca", "eor x0, x1, x2, lsl #1"),
    (b"\x20\x20\x02\xca", "eor x0, x1, x2, lsl #8"),
    (b"\x20\x40\x02\xca", "eor x0, x1, x2, lsl #16"),
    (b"\x20\x80\x02\xca", "eor x0, x1, x2, lsl #32"),
    (b"\x20\x84\x02\xca", "eor x0, x1, x2, lsl #33"),
    (b"\x20\x88\x02\xca", "eor x0, x1, x2, lsl #34"),
    (b"\x20\x00\x42\xca", "eor x0, x1, x2, lsr #0"),
    (b"\x20\x04\x42\xca", "eor x0, x1, x2, lsr #1"),
    (b"\x20\x20\x42\xca", "eor x0, x1, x2, lsr #8"),
    (b"\x20\x40\x42\xca", "eor x0, x1, x2, lsr #16"),
    (b"\x20\x80\x42\xca", "eor x0, x1, x2, lsr #32"),
    (b"\x20\x84\x42\xca", "eor x0, x1, x2, lsr #33"),
    (b"\x20\x88\x42\xca", "eor x0, x1, x2, lsr #34"),
    (b"\x20\x20\x82\xca", "eor x0, x1, x2, asr #8"),
    (b"\x20\x40\x82\xca", "eor x0, x1, x2, asr #16"),
    (b"\x20\x80\x82\xca", "eor x0, x1, x2, asr #32"),
    (b"\x20\x84\x82\xca", "eor x0, x1, x2, asr #33"),
    (b"\x20\x88\x82\xca", "eor x0, x1, x2, asr #34"),
    (b"\x20\x88\x82\xca", "eor x0, x1, x2, asr #34"),
    (b"\x20\x1c\x40\xd2", "eor x0, x1, #255"),
    (b"\x20\x18\x40\xd2", "eor x0, x1, #0x7f"),
    (b"\x20\x00\x40\xd2", "eor x0, x1, #1"),

    (b"\x20\x00\x22\xca", "eon x0, x1, x2, lsl #0"),
    (b"\x20\x04\x22\xca", "eon x0, x1, x2, lsl #1"),
    (b"\x20\x20\x22\xca", "eon x0, x1, x2, lsl #8"),
    (b"\x20\x40\x22\xca", "eon x0, x1, x2, lsl #16"),
    (b"\x20\x80\x22\xca", "eon x0, x1, x2, lsl #32"),
    (b"\x20\x84\x22\xca", "eon x0, x1, x2, lsl #33"),
    (b"\x20\x88\x22\xca", "eon x0, x1, x2, lsl #34"),
    (b"\x20\x00\x62\xca", "eon x0, x1, x2, lsr #0"),
    (b"\x20\x04\x62\xca", "eon x0, x1, x2, lsr #1"),
    (b"\x20\x20\x62\xca", "eon x0, x1, x2, lsr #8"),
    (b"\x20\x40\x62\xca", "eon x0, x1, x2, lsr #16"),
    (b"\x20\x80\x62\xca", "eon x0, x1, x2, lsr #32"),
    (b"\x20\x84\x62\xca", "eon x0, x1, x2, lsr #33"),
    (b"\x20\x88\x62\xca", "eon x0, x1, x2, lsr #34"),
    (b"\x20\x20\xa2\xca", "eon x0, x1, x2, asr #8"),
    (b"\x20\x40\xa2\xca", "eon x0, x1, x2, asr #16"),
    (b"\x20\x80\xa2\xca", "eon x0, x1, x2, asr #32"),
    (b"\x20\x84\xa2\xca", "eon x0, x1, x2, asr #33"),
    (b"\x20\x88\xa2\xca", "eon x0, x1, x2, asr #34"),
    (b"\x20\x88\xa2\xca", "eon x0, x1, x2, asr #34"),

    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x00\x22\xaa", "orn x0, x1, x2"),
    (b"\x40\x00\x21\xaa", "orn x0, x2, x1"),
    (b"\x41\x00\x20\xaa", "orn x1, x2, x0"),
    (b"\x01\x00\x22\xaa", "orn x1, x0, x2"),
    (b"\x20\x04\x22\xaa", "orn x0, x1, x2, lsl #1"),
    (b"\x20\x08\x22\xaa", "orn x0, x1, x2, lsl #2"),
    (b"\x20\x0c\x22\xaa", "orn x0, x1, x2, lsl #3"),
    (b"\x20\x04\xe2\xaa", "orn x0, x1, x2, ror #1"),
    (b"\x20\x08\xe2\xaa", "orn x0, x1, x2, ror #2"),
    (b"\x20\x0c\xe2\xaa", "orn x0, x1, x2, ror #3"),

    (b"\x82\x46\x82\xd2", "movz x2, #0x1234"),
    (b"\x01\xcf\x8a\xd2", "movz x1, #0x5678"),
    (b"\x20\x00\x02\xaa", "orr x0, x1, x2"),
    (b"\x40\x00\x01\xaa", "orr x0, x2, x1"),
    (b"\x41\x00\x00\xaa", "orr x1, x2, x0"),
    (b"\x01\x00\x02\xaa", "orr x1, x0, x2"),
    (b"\x20\x04\x02\xaa", "orr x0, x1, x2, lsl #1"),
    (b"\x20\x08\x02\xaa", "orr x0, x1, x2, lsl #2"),
    (b"\x20\x0c\x02\xaa", "orr x0, x1, x2, lsl #3"),
    (b"\x20\x04\xc2\xaa", "orr x0, x1, x2, ror #1"),
    (b"\x20\x08\xc2\xaa", "orr x0, x1, x2, ror #2"),
    (b"\x20\x0c\xc2\xaa", "orr x0, x1, x2, ror #3"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\x00\x40\xf9", "ldr x5, [x1]"),
    (b"\x26\x04\x40\xf8", "ldr x6, [x1], #0"),
    (b"\x27\x44\x40\xf8", "ldr x7, [x1], #4"),
    (b"\x28\x68\x62\xf8", "ldr x8, [x1, x2]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\x24\x5e\xf8", "ldr x9, [x1], #-30"),
    (b"\x2a\x8c\x40\xf8", "ldr x10, [x1, #8]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\x03\x40\xf9", "ldr x11, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\x00\x40\x39", "ldrb w5, [x1]"),
    (b"\x26\x04\x40\x38", "ldrb w6, [x1], #0"),
    (b"\x27\x44\x40\x38", "ldrb w7, [x1], #4"),
    (b"\x28\x68\x62\x38", "ldrb w8, [x1, x2]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\x24\x5e\x38", "ldrb w9, [x1], #-30"),
    (b"\x2a\x8c\x40\x38", "ldrb w10, [x1, #8]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\x03\x40\x39", "ldrb w11, [sp]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #0x90"),
    (b"\x2d\x48\x62\x38", "ldrb w13, [x1, w2, uxtw]"),
    (b"\x2d\xc8\x62\x78", "ldrh w13, [x1, w2, sxtw]"),
    (b"\x2d\x58\x62\xf8", "ldr x13, [x1, w2, uxtw #3]"),
    (b"\x2d\xd8\x62\xf8", "ldr x13, [x1, w2, sxtw #3]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\x00\x40\x79", "ldrh w5, [x1]"),
    (b"\x26\x04\x40\x78", "ldrh w6, [x1], #0"),
    (b"\x27\x44\x40\x78", "ldrh w7, [x1], #4"),
    (b"\x28\x68\x62\x78", "ldrh w8, [x1, x2]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\x24\x5e\x78", "ldrh w9, [x1], #-30"),
    (b"\x2a\x8c\x40\x78", "ldrh w10, [x1, #8]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\x03\x40\x79", "ldrh w11, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x24\x14\x40\xa9", "ldp x4, x5, [x1]"),
    (b"\x25\x18\xc0\xa8", "ldp x5, x6, [x1], #0"),
    (b"\x26\x9c\xc0\xa8", "ldp x6, x7, [x1], #8"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x28\x24\xfe\xa8", "ldp x8, x9, [x1], #-32"),
    (b"\x29\x28\xc1\xa9", "ldp x9, x10, [x1, #16]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xea\x2f\x40\xa9", "ldp x10, x11, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x24\x14\x40\x29", "ldp w4, w5, [x1]"),
    (b"\x25\x18\xc0\x28", "ldp w5, w6, [x1], #0"),
    (b"\x26\x1c\xc1\x28", "ldp w6, w7, [x1], #8"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x28\x24\xfc\x28", "ldp w8, w9, [x1], #-32"),
    (b"\x29\x28\xc2\x29", "ldp w9, w10, [x1, #16]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xea\x2f\x40\x29", "ldp w10, w11, [sp]"),

    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x21\x30\x00\x91", "add x1, x1, #12"), # STACK+12
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x10\x40\xf8", "ldur x0, [x1, #1]"),
    (b"\x20\x20\x40\xf8", "ldur x0, [x1, #2]"),
    (b"\x20\x30\x40\xf8", "ldur x0, [x1, #3]"),
    (b"\x20\x40\x40\xf8", "ldur x0, [x1, #4]"),
    (b"\x20\xf0\x5f\xf8", "ldur x0, [x1, #-1]"),
    (b"\x20\xe0\x5f\xf8", "ldur x0, [x1, #-2]"),
    (b"\x20\xd0\x5f\xf8", "ldur x0, [x1, #-3]"),
    (b"\x20\xc0\x5f\xf8", "ldur x0, [x1, #-4]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x40\x38", "ldurb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x10\x40\x38", "ldurb w0, [x1, #1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x20\x40\x38", "ldurb w0, [x1, #2]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x30\x40\x38", "ldurb w0, [x1, #3]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x40\x40\x38", "ldurb w0, [x1, #4]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xf0\x5f\x38", "ldurb w0, [x1, #0xffffffffffffffff]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xe0\x5f\x38", "ldurb w0, [x1, #0xfffffffffffffffe]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xd0\x5f\x38", "ldurb w0, [x1, #0xfffffffffffffffd]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xc0\x5f\x38", "ldurb w0, [x1, #0xfffffffffffffffc]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x40\x78", "ldurh w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x10\x40\x78", "ldurh w0, [x1, #1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x20\x40\x78", "ldurh w0, [x1, #2]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x30\x40\x78", "ldurh w0, [x1, #3]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x40\x40\x78", "ldurh w0, [x1, #4]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xf0\x5f\x78", "ldurh w0, [x1, #0xffffffffffffffff]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xe0\x5f\x78", "ldurh w0, [x1, #0xfffffffffffffffe]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xd0\x5f\x78", "ldurh w0, [x1, #0xfffffffffffffffd]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\xc0\x5f\x78", "ldurh w0, [x1, #0xfffffffffffffffc]"),

    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x21\x30\x00\x91", "add x1, x1, #12"), # STACK+12
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x38", "ldursb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x38", "ldursb x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x38", "ldursb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x78", "ldursh w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x78", "ldursh x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\xb8", "ldursw x0, [x1]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x38", "ldursb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x38", "ldursb x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x38", "ldursb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x78", "ldursh w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x78", "ldursh x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\xb8", "ldursw x0, [x1]"),

    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x21\x30\x00\x91", "add x1, x1, #12"), # STACK+12
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x39", "ldrsb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x39", "ldrsb x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x39", "ldrsb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x79", "ldrsh w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x79", "ldrsh x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\xb9", "ldrsw x0, [x1]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x39", "ldrsb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x39", "ldrsb x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x39", "ldrsb w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\xc0\x79", "ldrsh w0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\x79", "ldrsh x0, [x1]"),
    (b"\x20\x00\x40\xf8", "ldur x0, [x1]"),
    (b"\x20\x00\x80\xb9", "ldrsw x0, [x1]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x06\xa0\xd2", "movz x2, #0x30, lsl #16"), # HEAP address
    (b"\x42\x78\x00\x91", "add x2, x2, #30"),
    (b"\x23\x00\x40\xf8", "ldur x3, [x1]"),
    (b"\x44\x00\x40\xf8", "ldur x4, [x2]"),
    (b"\x60\x00\xc4\x93", "extr x0, x3, x4, #0"),
    (b"\x60\x04\xc4\x93", "extr x0, x3, x4, #1"),
    (b"\x60\x08\xc4\x93", "extr x0, x3, x4, #2"),
    (b"\x60\x0c\xc4\x93", "extr x0, x3, x4, #2"),
    (b"\x60\x78\xc4\x93", "extr x0, x3, x4, #30"),
    (b"\x60\xfc\xc4\x93", "extr x0, x3, x4, #63"),
    (b"\x60\x00\x84\x13", "extr w0, w3, w4, #0"),
    (b"\x60\x04\x84\x13", "extr w0, w3, w4, #1"),
    (b"\x60\x08\x84\x13", "extr w0, w3, w4, #2"),
    (b"\x60\x0c\x84\x13", "extr w0, w3, w4, #3"),
    (b"\x60\x7c\x84\x13", "extr w0, w3, w4, #31"),

    (b"\x01\x00\x00\x14", "b #4"),
    #b("\x02\x00\x00\x14", "b #8"),          # FIXME cannot handle this with
    #b("\x03\x00\x00\x14", "b #12"),         # unicorn emulating only one
    #b("\x00\xd0\x48\x14", "b #0x1234000"),  # instruction...
    #b("\x74\xbb\xff\x17", "b #-0x11230"),   #
    (b"\x20\x00\x00\x54" ,"b.eq #4"),
    #b("\x40\x00\x00\x54" ,"b.eq #8"),
    (b"\x01\x00\x00\x94" ,"bl #4"),

    (b"\x80\x0c\x90\xb7", "tbnz x0, #0x32, #0x190"),
    (b"\x20\x00\x90\xb6", "tbz x0, #0x32, #4"),

    (b"\x01\x00\x80\xd2", "movz x1, #0"),
    (b"\x02\x06\xa0\xd2", "movz x2, #0x20, lsl #16"), # STACK address
    (b"\xe1\x03\x02\xaa", "mov x1, x2"),
    (b"\x3f\x00\x00\x91", "mov sp, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xe0\x03\x21\xaa", "mvn x0, x1"),
    (b"\xe0\x03\x01\xcb", "neg x0, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x63\xa0\x84\xd2", "movz x3, #9475"),
    (b"\x20\x0c\x02\x9b", "madd x0, x1, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),
    (b"\x00\x0c\x02\x9b", "madd x0, x0, x2, x3"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x7c\x02\x9b", "mul x0, x1, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),
    (b"\x00\x7c\x02\x9b", "mul x0, x0, x2"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x63\xa0\x84\xd2", "movz x3, #9475"),
    (b"\x20\x8c\x02\x9b", "msub x0, x1, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),
    (b"\x00\x8c\x02\x9b", "msub x0, x0, x2, x3"),


    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\xfc\x02\x9b", "mneg x0, x1, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),
    (b"\x00\xfc\x02\x9b", "mneg x0, x0, x2"),

    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),
    (b"\x00\xfc\x02\x1b", "mneg w0, w0, w2"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x63\xa0\x84\xd2", "movz x3, #9475"),
    (b"\x64\xa0\x84\xd2", "movz x4, #9475"),
    (b"\xe5\x24\x81\xd2", "movz x5, #2343"),
    (b"\xa6\xaf\x81\xd2", "movz x6, #3453"),
    (b"\x87\x3a\x82\xd2", "movz x7, #4564"),
    (b"\xe8\x16\x84\xd2", "movz x8, #8375"),
    (b"\xe9\xc1\x84\xd2", "movz x9, #9743"),
    (b"\xea\xaa\x82\xd2", "movz x10, #5463"),
    (b"\x2b\xf8\x80\xd2", "movz x11, #1985"),
    (b"\x25\x00\x00\xf9", "str x5, [x1]"),
    (b"\x26\x04\x00\xf8", "str x6, [x1], #0"),
    (b"\x27\x44\x00\xf8", "str x7, [x1], #4"),
    (b"\x28\x68\x22\xf8", "str x8, [x1, x2]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\x24\x1e\xf8", "str x9, [x1], #-30"),
    (b"\x2a\x8c\x00\xf8", "str x10, [x1, #8]!"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\x03\x00\xf9", "str x11, [sp]"),
    (b"\x25\x00\x00\xf8", "stur x5, [x1]"),
    (b"\x26\x00\x00\x38", "sturb w6, [x1]"),
    (b"\x27\x00\x00\x78", "sturh w7, [x1]"),
    (b"\x29\x00\x00\xf9", "str x9, [x1]"),
    (b"\x2a\x00\x00\x39", "strb w10, [x1]"),
    (b"\x2b\x00\x00\x79", "strh w11, [x1]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\xe5\x24\x81\xd2", "movz x5, #2343"),
    (b"\xa6\xaf\x81\xd2", "movz x6, #3453"),
    (b"\x87\x3a\x82\xd2", "movz x7, #4564"),
    (b"\xe8\x16\x84\xd2", "movz x8, #8375"),
    (b"\xe9\xc1\x84\xd2", "movz x9, #9743"),
    (b"\xea\xaa\x82\xd2", "movz x10, #5463"),
    (b"\x25\x18\x00\xa9", "stp x5, x6, [x1]"),
    (b"\x27\x20\x80\xa8", "stp x7, x8, [x1], #0"),
    (b"\x29\xa8\x80\xa8", "stp x9, x10, [x1], #8"),
    (b"\x25\x20\x82\xa9", "stp x5, x8, [x1, #32]!"),
    (b"\x26\x1c\x01\xa9", "stp x6, x7, [x1, #16]"),
    (b"\x25\x18\x00\x29", "stp w5, w6, [x1]"),
    (b"\x27\x20\x80\x28", "stp w7, w8, [x1], #0"),
    (b"\x29\x28\x81\x28", "stp w9, w10, [x1], #8"),
    (b"\x25\x20\x84\x29", "stp w5, w8, [x1, #32]!"),
    (b"\x26\x1c\x02\x29", "stp w6, w7, [x1, #16]"),

    (b"\xc1\xbd\x9b\xd2", "movz x1, #0xddee"),
    (b"\x20\x1c\x40\x93", "sxtb x0, x1"),
    (b"\x20\x3c\x40\x93", "sxth x0, x1"),
    (b"\x20\x7c\x40\x93", "sxtw x0, x1"),
    (b"\x20\x1c\x00\x53", "uxtb w0, w1"),
    (b"\x20\x3c\x00\x53", "uxth w0, w1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x00\x82\x9a", "csel x0, x1, x2, eq"),
    (b"\x40\x00\x81\x9a", "csel x0, x2, x1, eq"),
    (b"\x20\x10\x82\x9a", "csel x0, x1, x2, ne"),
    (b"\x40\x10\x81\x9a", "csel x0, x2, x1, ne"),

    (b"\x20\x04\x82\x9a", "csinc x0, x1, x2, eq"),
    (b"\x40\x04\x81\x9a", "csinc x0, x2, x1, eq"),
    (b"\x20\x14\x82\x9a", "csinc x0, x1, x2, ne"),
    (b"\x40\x14\x81\x9a", "csinc x0, x2, x1, ne"),

    (b"\x20\x04\x82\xda", "csneg x0, x1, x2, eq"),
    (b"\x40\x04\x81\xda", "csneg x0, x2, x1, eq"),
    (b"\x20\x14\x82\xda", "csneg x0, x1, x2, ne"),
    (b"\x40\x14\x81\xda", "csneg x0, x2, x1, ne"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\x20\xf8\x7f\xd3", "lsl x0, x1, #1"),
    (b"\x20\xf4\x7e\xd3", "lsl x0, x1, #2"),
    (b"\x20\xf0\x7d\xd3", "lsl x0, x1, #3"),
    (b"\x20\xec\x7c\xd3", "lsl x0, x1, #4"),
    (b"\x20\xfc\x41\xd3", "lsr x0, x1, #1"),
    (b"\x20\xfc\x42\xd3", "lsr x0, x1, #2"),
    (b"\x20\xfc\x43\xd3", "lsr x0, x1, #3"),
    (b"\x20\xfc\x44\xd3", "lsr x0, x1, #4"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x20\xc2\x9a", "lsl x0, x1, x2"),
    (b"\x20\x24\xc2\x9a", "lsr x0, x1, x2"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xeb", "cmp x1, x2"),
    (b"\x5f\x00\x01\xeb", "cmp x2, x1"),
    (b"\x01\x00\x80\xd2", "movz x1, #0"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xeb", "cmp x1, x2"),
    (b"\x5f\x00\x01\xeb", "cmp x2, x1"),
    (b"\x01\x00\x80\xd2", "movz x1, #0"),
    (b"\x02\x00\x80\xd2", "movz x2, #0"),
    (b"\x3f\x00\x02\xeb", "cmp x1, x2"),
    (b"\x5f\x00\x01\xeb", "cmp x2, x1"),
    (b"\xc1\x88\x83\xd2", "movz x1, #7238"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xeb", "cmp x1, x2"),
    (b"\x5f\x00\x01\xeb", "cmp x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xab", "cmn x1, x2"),
    (b"\x5f\x00\x01\xab", "cmn x2, x1"),
    (b"\x01\x00\x80\xd2", "movz x1, #0"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xab", "cmn x1, x2"),
    (b"\x5f\x00\x01\xab", "cmn x2, x1"),
    (b"\x01\x00\x80\xd2", "movz x1, #0"),
    (b"\x02\x00\x80\xd2", "movz x2, #0"),
    (b"\x3f\x00\x02\xab", "cmn x1, x2"),
    (b"\x5f\x00\x01\xab", "cmn x2, x1"),
    (b"\xc1\x88\x83\xd2", "movz x1, #7238"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x3f\x00\x02\xab", "cmn x1, x2"),
    (b"\x5f\x00\x01\xab", "cmn x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x63\xa0\x84\xd2", "movz x3, #9475"),
    (b"\x20\x0c\xa2\x9b", "umaddl x0, w1, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),
    (b"\x00\x0c\xa2\x9b", "umaddl x0, w0, w2, x3"),

    (b"\x20\x8c\xa2\x9b", "umsubl x0, w1, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),
    (b"\x00\x8c\xa2\x9b", "umsubl x0, w0, w2, x3"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\x42\xd5\xbd\xd2", "movz x2, #0xeeaa, lsl #16"),
    (b"\xa3\xd5\x9b\xd2", "movz x3, #0xdead"),
    (b"\x20\x0c\x22\x9b", "smaddl x0, w1, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),
    (b"\x00\x0c\x22\x9b", "smaddl x0, w0, w2, x3"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\x42\xd5\xbd\xd2", "movz x2, #0xeeaa, lsl #16"),
    (b"\xa3\xd5\x9b\xd2", "movz x3, #0xdead"),
    (b"\x20\x8c\x22\x9b", "smsubl x0, w1, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),
    (b"\x00\x8c\x22\x9b", "smsubl x0, w0, w2, x3"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\x42\xd5\xbd\xd2", "movz x2, #0xeeaa, lsl #16"),
    (b"\x20\x7c\x22\x9b", "smull x0, w1, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),
    (b"\x00\x7c\x22\x9b", "smull x0, w0, w2"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\x42\xd5\xbd\xd2", "movz x2, #0xeeaa, lsl #16"),
    (b"\x20\x7c\x42\x9b", "smulh x0, x1, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),
    (b"\x00\x7c\x42\x9b", "smulh x0, x0, x2"),

    (b"\x01\x06\xa0\x92", "movn x1, #0x30, lsl #16"),
    (b"\x02\x02\x80\x92", "movn x2, #16"),
    (b"\x63\xa0\x84\x92", "movn x3, #9475"),
    (b"\x64\xa0\x84\x92", "movn x4, #9475"),
    (b"\xe5\x24\x81\x92", "movn x5, #2343"),
    (b"\xa6\xaf\x81\x92", "movn x6, #3453"),
    (b"\x87\x3a\x82\x92", "movn x7, #4564"),
    (b"\xe8\x16\x84\x92", "movn x8, #8375"),
    (b"\xe9\xc1\x84\x92", "movn x9, #9743"),
    (b"\xea\xaa\x82\x92", "movn x10, #5463"),
    (b"\x2b\xf8\x80\x92", "movn x11, #1985"),

    (b"\xc1\xfd\xff\xd2", "movz x1, #0xffee, lsl #48"),
    (b"\x81\xb9\xdb\xf2", "movk x1, #0xddcc, lsl #32"),
    (b"\x41\x75\xb7\xf2", "movk x1, #0xbbaa, lsl #16"),
    (b"\x01\x31\x93\xf2", "movk x1, #0x9988"),
    (b"\x20\x00\x40\xd3", "ubfx x0, x1, #0, #1"),
    (b"\x20\x08\x40\xd3", "ubfx x0, x1, #0, #3"),
    (b"\x20\x0c\x40\xd3", "ubfx x0, x1, #0, #4"),
    (b"\x20\x10\x40\xd3", "ubfx x0, x1, #0, #5"),
    (b"\x20\x78\x40\xd3", "ubfx x0, x1, #0, #31"),
    (b"\x20\xf8\x40\xd3", "ubfx x0, x1, #0, #63"),
    (b"\x20\xfc\x40\xd3", "ubfx x0, x1, #0, #64"),
    (b"\x20\xfc\x41\xd3", "ubfx x0, x1, #1, #63"),
    (b"\x20\xfc\x42\xd3", "ubfx x0, x1, #2, #62"),
    (b"\x20\xfc\x43\xd3", "ubfx x0, x1, #3, #61"),
    (b"\x20\xfc\x60\xd3", "ubfx x0, x1, #32, #32"),
    (b"\x20\x4c\x4a\xd3", "ubfx x0, x1, #10, #10"),

    (b"\xc1\xfd\xff\xd2", "movz x1, #0xffee, lsl #48"),
    (b"\x81\xb9\xdb\xf2", "movk x1, #0xddcc, lsl #32"),
    (b"\x41\x75\xb7\xf2", "movk x1, #0xbbaa, lsl #16"),
    (b"\x01\x31\x93\xf2", "movk x1, #0x9988"),
    (b"\x20\x00\x40\x93", "sbfx x0, x1, #0, #1"),
    (b"\x20\x08\x40\x93", "sbfx x0, x1, #0, #3"),
    (b"\x20\x0c\x40\x93", "sbfx x0, x1, #0, #4"),
    (b"\x20\x10\x40\x93", "sbfx x0, x1, #0, #5"),
    (b"\x20\x78\x40\x93", "sbfx x0, x1, #0, #31"),
    (b"\x20\xf8\x40\x93", "sbfx x0, x1, #0, #63"),
    (b"\x20\xfc\x40\x93", "sbfx x0, x1, #0, #64"),
    (b"\x20\xfc\x41\x93", "sbfx x0, x1, #1, #63"),
    (b"\x20\xfc\x42\x93", "sbfx x0, x1, #2, #62"),
    (b"\x20\xfc\x43\x93", "sbfx x0, x1, #3, #61"),
    (b"\x20\xfc\x60\x93", "sbfx x0, x1, #32, #32"),
    (b"\x20\x4c\x4a\x93", "sbfx x0, x1, #10, #10"),
    (b"\x20\x48\x49\x93", "sbfx x0, x1, #9, #10"),
    (b"\x20\x40\x47\x93", "sbfx x0, x1, #7, #10"),
    (b"\x20\x3c\x47\x93", "sbfx x0, x1, #7, #9"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\x42\xd5\xbd\xd2", "movz x2, #0xeeaa, lsl #16"),

    (b"\x20\x00\x42\xfa", "ccmp x1, x2, 0, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x21\x00\x42\xfa", "ccmp x1, x2, 1, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x22\x00\x42\xfa", "ccmp x1, x2, 2, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x23\x00\x42\xfa", "ccmp x1, x2, 3, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x24\x00\x42\xfa", "ccmp x1, x2, 4, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x25\x00\x42\xfa", "ccmp x1, x2, 5, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x26\x00\x42\xfa", "ccmp x1, x2, 6, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x27\x00\x42\xfa", "ccmp x1, x2, 7, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x28\x00\x42\xfa", "ccmp x1, x2, 8, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x29\x00\x42\xfa", "ccmp x1, x2, 9, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2a\x00\x42\xfa", "ccmp x1, x2, 10, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2b\x00\x42\xfa", "ccmp x1, x2, 11, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2c\x00\x42\xfa", "ccmp x1, x2, 12, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2d\x00\x42\xfa", "ccmp x1, x2, 13, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2e\x00\x42\xfa", "ccmp x1, x2, 14, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2f\x00\x42\xfa", "ccmp x1, x2, 15, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\xc1\xfd\xbf\xd2", "movz x1, #0xffee, lsl #16"),
    (b"\xc2\xfd\xbf\xd2", "movz x2, #0xffee, lsl #16"),

    (b"\x20\x00\x42\xfa", "ccmp x1, x2, 0, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x21\x00\x42\xfa", "ccmp x1, x2, 1, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x22\x00\x42\xfa", "ccmp x1, x2, 2, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x23\x00\x42\xfa", "ccmp x1, x2, 3, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x24\x00\x42\xfa", "ccmp x1, x2, 4, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x25\x00\x42\xfa", "ccmp x1, x2, 5, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x26\x00\x42\xfa", "ccmp x1, x2, 6, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x27\x00\x42\xfa", "ccmp x1, x2, 7, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x28\x00\x42\xfa", "ccmp x1, x2, 8, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x29\x00\x42\xfa", "ccmp x1, x2, 9, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2a\x00\x42\xfa", "ccmp x1, x2, 10, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2b\x00\x42\xfa", "ccmp x1, x2, 11, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2c\x00\x42\xfa", "ccmp x1, x2, 12, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2d\x00\x42\xfa", "ccmp x1, x2, 13, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2e\x00\x42\xfa", "ccmp x1, x2, 14, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x2f\x00\x42\xfa", "ccmp x1, x2, 15, eq"),
    (b"\xe0\x17\x9f\x9a", "cset x0, eq"),
    (b"\xe0\xb7\x9f\x9a", "cset x0, ge"),
    (b"\xe0\xd7\x9f\x9a", "cset x0, gt"),
    (b"\xe0\x97\x9f\x9a", "cset x0, hi"),
    (b"\xe0\x37\x9f\x9a", "cset x0, hs"),
    (b"\xe0\xc7\x9f\x9a", "cset x0, le"),
    (b"\xe0\x27\x9f\x9a", "cset x0, lo"),
    (b"\xe0\x87\x9f\x9a", "cset x0, ls"),
    (b"\xe0\xa7\x9f\x9a", "cset x0, lt"),
    (b"\xe0\x57\x9f\x9a", "cset x0, mi"),
    (b"\xe0\x07\x9f\x9a", "cset x0, ne"),
    (b"\xe0\x47\x9f\x9a", "cset x0, pl"),
    (b"\xe0\x67\x9f\x9a", "cset x0, vc"),
    (b"\xe0\x77\x9f\x9a", "cset x0, vs"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x41\x14\x82\x9a", "cinc x1, x2, eq"),
    (b"\x41\x04\x82\x9a", "cinc x1, x2, ne"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\xc1\xfd\xff\xd2", "movz x1, #0xffee, lsl #48"),
    (b"\x81\xb9\xdb\xf2", "movk x1, #0xddcc, lsl #32"),
    (b"\x41\x75\xb7\xf2", "movk x1, #0xbbaa, lsl #16"),
    (b"\x01\x31\x93\xf2", "movk x1, #0x9988"),
    (b"\x20\xfc\x40\xd3", "ubfiz x0, x1, #0, #64"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xf8\x7f\xd3", "ubfiz x0, x1, #1, #63"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xf4\x7e\xd3", "ubfiz x0, x1, #2, #62"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xf0\x7d\xd3", "ubfiz x0, x1, #3, #61"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xec\x7c\xd3", "ubfiz x0, x1, #4, #60"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xe8\x7b\xd3", "ubfiz x0, x1, #5, #59"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xe4\x7a\xd3", "ubfiz x0, x1, #6, #58"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xe0\x79\xd3", "ubfiz x0, x1, #7, #57"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\xdc\x78\xd3", "ubfiz x0, x1, #8, #56"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x7c\x7a\xd3", "ubfiz x0, x1, #6, #32"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x00\x78\xd3", "ubfiz x0, x1, #8, #1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x00\x41\xd3", "ubfiz x0, x1, #63, #1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x00\x18\x53", "ubfiz w0, w1, #8, #1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x00\x01\x53", "ubfiz w0, w1, #31, #1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x00\x04\x00\xd1", "sub x0, x0, #1"),
    (b"\x20\x7c\x00\x53", "ubfiz w0, w1, #0, #32"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x08\xc2\x9a", "udiv x0, x1, x2"),
    (b"\x40\x08\xc1\x9a", "udiv x0, x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\x02\x00\x80\xd2", "movz x2, #0"),
    (b"\x20\x08\xc2\x9a", "udiv x0, x1, x2"),
    (b"\x40\x08\xc1\x9a", "udiv x0, x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x0c\xc2\x9a", "sdiv x0, x1, x2"),
    (b"\x40\x0c\xc1\x9a", "sdiv x0, x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\x02\x00\x80\xd2", "movz x2, #0"),
    (b"\x20\x0c\xc2\x9a", "sdiv x0, x1, x2"),
    (b"\x40\x0c\xc1\x9a", "sdiv x0, x2, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x7c\xa2\x9b", "umull x0, w1, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),
    (b"\x00\x7c\xa2\x9b", "umull x0, w0, w2"),

    (b"\xc1\xfd\xff\xd2", "movz x1, #0xffee, lsl #48"),
    (b"\x81\xb9\xdb\xf2", "movk x1, #0xddcc, lsl #32"),
    (b"\x41\x75\xb7\xf2", "movk x1, #0xbbaa, lsl #16"),
    (b"\x01\x31\x93\xf2", "movk x1, #0x9988"),
    (b"\x20\x7c\xc1\x9b", "umulh x0, x1, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),
    (b"\x00\x7c\xc1\x9b", "umulh x0, x0, x1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\xfc\xa2\x9b", "umnegl x0, w1, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),
    (b"\x00\xfc\xa2\x9b", "umnegl x0, w0, w2"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x2c\xc2\x9a", "ror x0, x1, x2"),
    (b"\x40\x2c\xc1\x9a", "ror x0, x2, x1"),
    (b"\x40\x00\xc2\x93", "ror x0, x2, #0"),
    (b"\x40\x04\xc2\x93", "ror x0, x2, #1"),
    (b"\x40\x08\xc2\x93", "ror x0, x2, #2"),
    (b"\x40\x0c\xc2\x93", "ror x0, x2, #3"),
    (b"\x40\x10\xc2\x93", "ror x0, x2, #4"),
    (b"\x40\xf8\xc2\x93", "ror x0, x2, #62"),
    (b"\x40\xfc\xc2\x93", "ror x0, x2, #63"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\x80\xd2", "mov x1, #0"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x41\x00\x80\xd2", "mov x1, #1 << 1"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x81\x00\x80\xd2", "mov x1, #1 << 2"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\x82\xd2", "mov x1, #1 << 12"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\x82\xd2", "mov x1, #1 << 12"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\xb0\xd2", "mov x1, #1 << 31"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x21\x00\xc0\xd2", "mov x1, #1 << 32"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x41\x00\xc0\xd2", "mov x1, #1 << 33"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\xe8\xd2", "mov x1, #1 << 62"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x01\x00\xf0\xd2", "mov x1, #1 << 63"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x00\x00\x80\x92", "movn x0, #0"),
    (b"\x21\x00\x80\xd2", "mov x1, #1 << 64"),
    (b"\x20\x10\xc0\xda", "clz x0, x1"),
    (b"\x20\x10\xc0\x5a", "clz w0, w1"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\xdf\xc8", "ldar x5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\xfc\xdf\xc8", "ldar x9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\xdf\xc8", "ldar x11, [sp]"),
    (b"\xff\xff\xdf\xc8", "ldar xzr, [sp]"),
    (b"\xe7\xff\xdf\x88", "ldar w7, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\xdf\x08", "ldarb w5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\xfc\xdf\x08", "ldarb w9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\xdf\x08", "ldarb w11, [sp]"),
    (b"\xff\xff\xdf\x08", "ldarb wzr, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\xdf\x48", "ldarh w5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\xfc\xdf\x48", "ldarh w9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\xdf\x48", "ldarh w11, [sp]"),
    (b"\xff\xff\xdf\x48", "ldarh wzr, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\x5f\xc8", "ldaxr x5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x29\xfc\x5f\xc8", "ldaxr x9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x20\x00\x91", "add sp, x1, #8"),
    (b"\xeb\xff\x5f\xc8", "ldaxr x11, [sp]"),
    (b"\xff\xff\x5f\xc8", "ldaxr xzr, [sp]"),
    (b"\xe7\xff\x5f\x88", "ldaxr w7, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\x5f\x08", "ldaxrb w5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\xfc\x5f\x08", "ldaxrb w9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\x5f\x08", "ldaxrb w11, [sp]"),
    (b"\xff\xff\x5f\x08", "ldaxrb wzr, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x25\xfc\x5f\x48", "ldaxrh w5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x29\xfc\x5f\x48", "ldaxrh w9, [x1]"),
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\x5f\x48", "ldaxrh w11, [sp]"),
    (b"\xff\xff\x5f\x48", "ldaxrh wzr, [sp]"),

    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x02\x02\x80\xd2", "movz x2, #16"),
    (b"\x63\xa0\x84\xd2", "movz x3, #9475"),
    (b"\x64\xa0\x84\xd2", "movz x4, #9475"),
    (b"\xe5\x24\x81\xd2", "movz x5, #2343"),
    (b"\xa6\xaf\x81\xd2", "movz x6, #3453"),
    (b"\x87\x3a\x82\xd2", "movz x7, #4564"),
    (b"\xe8\x16\x84\xd2", "movz x8, #8375"),
    (b"\xe9\xc1\x84\xd2", "movz x9, #9743"),
    (b"\xea\xaa\x82\xd2", "movz x10, #5463"),
    (b"\x2b\xf8\x80\xd2", "movz x11, #1985"),
    (b"\x25\xfc\x9f\xc8", "stlr x5, [x1]"),
    (b"\x01\x06\xa0\xd2", "movz x1, #0x30, lsl #16"), # HEAP address
    (b"\x21\xc8\x00\x91", "add x1, x1, #50"), # HEAP+50 address
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x3f\x10\x00\x91", "add sp, x1, #4"),
    (b"\xeb\xff\x9f\xc8", "stlr x11, [sp]"),
    (b"\x25\x00\x00\xf8", "stur x5, [x1]"),
    (b"\x26\x00\x00\x38", "sturb w6, [x1]"),
    (b"\x27\x00\x00\x78", "sturh w7, [x1]"),
    (b"\x29\xfc\x9f\xc8", "stlr x9, [x1]"),
    (b"\x2a\xfc\x9f\x08", "stlrb w10, [x1]"),
    (b"\x2b\xfc\x9f\x48", "stlrh w11, [x1]"),

    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x21\x20\x00\x91", "add x1, x1, #8"), # STACK+8
    (b"\x20\x7c\x5f\xc8", "ldxr x0, [x1]"),
    (b"\x21\x30\x00\x91", "add x1, x1, #12"), # STACK+24
    (b"\x20\x7c\x5f\x08", "ldxrb w0, [x1]"),
    (b"\x21\x30\x00\x91", "add x1, x1, #12"), # STACK+36
    (b"\x20\x7c\x5f\x48", "ldxrh w0, [x1]"),

    (b"\xc1\xfd\xff\xd2", "movz x1, #0xffee, lsl #48"),
    (b"\x81\xb9\xdb\xf2", "movk x1, #0xddcc, lsl #32"),
    (b"\x41\x75\xb7\xf2", "movk x1, #0xbbaa, lsl #16"),
    (b"\x01\x31\x93\xf2", "movk x1, #0x9988"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x0c\xc0\xda", "rev x0, x1"),
    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x08\xc0\x5a", "rev w0, w1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x04\xc0\xda", "rev16 x0, x1"),
    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x04\xc0\x5a", "rev16 w0, w1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x08\xc0\xda", "rev32 x0, x1"),

    (b"\x00\x00\x80\xd2", "movz x0, #0"),
    (b"\x20\x00\xc0\xda", "rbit x0, x1"),
    (b"\x20\x00\xc0\x5a", "rbit w0, w1"),

    (b"\x20\x00\x80\xd2", "movz x0, #1"),
    (b"\x20\x00\xc0\xda", "rbit x0, x1"),
    (b"\x20\x00\xc0\x5a", "rbit w0, w1"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x41\x14\x7d\xb3", "bfi x1, x2, 3, 6"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x41\x0c\x7f\xb3", "bfi x1, x2, 1, 4"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x41\x0c\x7f\xb3", "bfi x1, x2, 1, 4"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x41\x24\x7c\xb3", "bfi x1, x2, 4, 10"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x00\x3f\x8a", "bic x0, x1, xzr"),

    (b"\x41\x9a\x80\xd2", "movz x1, #1234"),
    (b"\xc2\x88\x83\xd2", "movz x2, #7238"),
    (b"\x20\x00\x3f\x8a", "bic x0, x1, x2"),

    (b"\x40\xf8\x7f\x92", "bic x0, x2, #1"),
    (b"\x40\xf8\x7e\x92", "bic x0, x2, #2"),
    (b"\x40\xf4\x7e\x92", "bic x0, x2, #3"),
    (b"\x40\xf8\x7d\x92", "bic x0, x2, #4"),
    (b"\x41\xf8\x7f\x92", "bic x1, x2, #1"),
    (b"\x41\xf8\x7e\x92", "bic x1, x2, #2"),
    (b"\x41\xf4\x7e\x92", "bic x1, x2, #3"),
    (b"\x41\xf8\x7d\x92", "bic x1, x2, #4"),
    (b"\x22\xf8\x7f\x92", "bic x2, x1, #1"),
    (b"\x22\xf8\x7e\x92", "bic x2, x1, #2"),
    (b"\x22\xf4\x7e\x92", "bic x2, x1, #3"),
    (b"\x22\xf8\x7d\x92", "bic x2, x1, #4"),

    (b"\x28\x00\x00\x37", "tbnz w8, #0, #4"),
    (b"\x48\x00\x00\x36", "tbz w8, #0, #0"),

    # Armv8-A Neon
    (b"\x01\x04\xa0\xd2", "movz x1, #0x20, lsl #16"), # STACK address
    (b"\x02\x01\x80\xd2", "movz x2, #0x8"),

    (b"\x20\x40\x40\x4c", "ld3 {v0.16b, v1.16b, v2.16b}, [x1]"),
    (b"\x20\x44\x40\x4c", "ld3 {v0.8h, v1.8h, v2.8h}, [x1]"),
    (b"\x20\x48\x40\x4c", "ld3 {v0.4s, v1.4s, v2.4s}, [x1]"),
    (b"\x20\x4c\x40\x4c", "ld3 {v0.2d, v1.2d, v2.2d}, [x1]"),
    (b"\x20\x40\x40\x0c", "ld3 {v0.8b, v1.8b, v2.8b}, [x1]"),
    (b"\x20\x44\x40\x0c", "ld3 {v0.4h, v1.4h, v2.4h}, [x1]"),
    (b"\x20\x48\x40\x0c", "ld3 {v0.2s, v1.2s, v2.2s}, [x1]"),
    (b"\x20\x40\xc2\x4c", "ld3 {v0.16b, v1.16b, v2.16b}, [x1], x2"),

    (b"\x20\x1c\x22\x6e", "eor v0.16b, v1.16b, v2.16b"),
    (b"\x20\x1c\x22\x2e", "eor v0.8b, v1.8b, v2.8b"),

    (b"\x20\x1c\x22\x4e", "and v0.16b, v1.16b, v2.16b"),
    (b"\x20\x1c\x22\x0e", "and v0.8b, v1.8b, v2.8b"),

    (b"\x20\xe0\x40\x4d", "ld3r {v0.16b, v1.16b, v2.16b}, [x1]"),
    (b"\x20\xe4\x40\x4d", "ld3r {v0.8h, v1.8h, v2.8h}, [x1]"),
    (b"\x20\xe8\x40\x4d", "ld3r {v0.4s, v1.4s, v2.4s}, [x1]"),
    (b"\x20\xec\x40\x4d", "ld3r {v0.2d, v1.2d, v2.2d}, [x1]"),
    (b"\x20\xe0\x40\x0d", "ld3r {v0.8b, v1.8b, v2.8b}, [x1]"),
    (b"\x20\xe4\x40\x0d", "ld3r {v0.4h, v1.4h, v2.4h}, [x1]"),
    (b"\x20\xe8\x40\x0d", "ld3r {v0.2s, v1.2s, v2.2s}, [x1]"),
    (b"\x20\xec\x40\x0d", "ld3r {v0.1d, v1.1d, v2.1d}, [x1]"),

    #(b"\x20\x40\xdf\x4c", "ld3 {v0.16b, v1.16b, v2.16b}, [x1], #48"),   # working on capstone 5.x but not on 4.x
    #(b"\x20\x44\xdf\x0c", "ld3 {v0.4h, v1.4h, v2.4h}, [x1], #24"),      # working on capstone 5.x but not on 4.x
    #(b"\x20\xe0\xdf\x4d", "ld3r {v0.16b, v1.16b, v2.16b}, [x1], #3"),   # working on capstone 5.x but not on 4.x
    #(b"\x20\xe4\xdf\x4d", "ld3r {v0.8h, v1.8h, v2.8h}, [x1], #6"),      # working on capstone 5.x but not on 4.x
    #(b"\x20\xe8\xdf\x4d", "ld3r {v0.4s, v1.4s, v2.4s}, [x1], #12"),     # working on capstone 5.x but not on 4.x
    #(b"\x20\xec\xdf\x4d", "ld3r {v0.2d, v1.2d, v2.2d}, [x1], #24"),     # working on capstone 5.x but not on 4.x
    #(b"\x20\xe0\xdf\x0d", "ld3r {v0.8b, v1.8b, v2.8b}, [x1], #3"),      # working on capstone 5.x but not on 4.x
    #(b"\x20\xe4\xdf\x0d", "ld3r {v0.4h, v1.4h, v2.4h}, [x1], #6"),      # working on capstone 5.x but not on 4.x
    #(b"\x20\xe8\xdf\x0d", "ld3r {v0.2s, v1.2s, v2.2s}, [x1], #12"),     # working on capstone 5.x but not on 4.x
    #(b"\x20\xec\xdf\x0d", "ld3r {v0.1d, v1.1d, v2.1d}, [x1], #24"),     # working on capstone 5.x but not on 4.x
]

def emu_with_unicorn(opcode, istate):
    # Initialize emulator in aarch64 mode
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

    # map memory for this emulation
    mu.mem_map(ADDR, SIZE)

    # write machine code to be emulated to memory
    index = 0
    for op, _ in CODE:
        mu.mem_write(ADDR+index, op)
        index += len(op)

    mu.mem_write(STACK,             bytes(istate['stack']))
    mu.mem_write(HEAP,              bytes(istate['heap']))
    mu.reg_write(UC_ARM64_REG_X0,   istate['x0'])
    mu.reg_write(UC_ARM64_REG_X1,   istate['x1'])
    mu.reg_write(UC_ARM64_REG_X2,   istate['x2'])
    mu.reg_write(UC_ARM64_REG_X3,   istate['x3'])
    mu.reg_write(UC_ARM64_REG_X4,   istate['x4'])
    mu.reg_write(UC_ARM64_REG_X5,   istate['x5'])
    mu.reg_write(UC_ARM64_REG_X6,   istate['x6'])
    mu.reg_write(UC_ARM64_REG_X7,   istate['x7'])
    mu.reg_write(UC_ARM64_REG_X8,   istate['x8'])
    mu.reg_write(UC_ARM64_REG_X9,   istate['x9'])
    mu.reg_write(UC_ARM64_REG_X10,  istate['x10'])
    mu.reg_write(UC_ARM64_REG_X11,  istate['x11'])
    mu.reg_write(UC_ARM64_REG_X12,  istate['x12'])
    mu.reg_write(UC_ARM64_REG_X13,  istate['x13'])
    mu.reg_write(UC_ARM64_REG_X14,  istate['x14'])
    mu.reg_write(UC_ARM64_REG_X15,  istate['x15'])
    mu.reg_write(UC_ARM64_REG_X16,  istate['x16'])
    mu.reg_write(UC_ARM64_REG_X17,  istate['x17'])
    mu.reg_write(UC_ARM64_REG_X18,  istate['x18'])
    mu.reg_write(UC_ARM64_REG_X19,  istate['x19'])
    mu.reg_write(UC_ARM64_REG_X20,  istate['x20'])
    mu.reg_write(UC_ARM64_REG_X21,  istate['x21'])
    mu.reg_write(UC_ARM64_REG_X22,  istate['x22'])
    mu.reg_write(UC_ARM64_REG_X23,  istate['x23'])
    mu.reg_write(UC_ARM64_REG_X24,  istate['x24'])
    mu.reg_write(UC_ARM64_REG_X25,  istate['x25'])
    mu.reg_write(UC_ARM64_REG_X26,  istate['x26'])
    mu.reg_write(UC_ARM64_REG_X27,  istate['x27'])
    mu.reg_write(UC_ARM64_REG_X28,  istate['x28'])
    mu.reg_write(UC_ARM64_REG_X29,  istate['x29'])
    mu.reg_write(UC_ARM64_REG_X30,  istate['x30'])
    mu.reg_write(UC_ARM64_REG_V0,   istate['v0'])
    mu.reg_write(UC_ARM64_REG_V1,   istate['v1'])
    mu.reg_write(UC_ARM64_REG_V2,   istate['v2'])
    mu.reg_write(UC_ARM64_REG_V3,   istate['v3'])
    mu.reg_write(UC_ARM64_REG_V4,   istate['v4'])
    mu.reg_write(UC_ARM64_REG_V5,   istate['v5'])
    mu.reg_write(UC_ARM64_REG_V6,   istate['v6'])
    mu.reg_write(UC_ARM64_REG_V7,   istate['v7'])
    mu.reg_write(UC_ARM64_REG_V8,   istate['v8'])
    mu.reg_write(UC_ARM64_REG_V9,   istate['v9'])
    mu.reg_write(UC_ARM64_REG_V10,  istate['v10'])
    mu.reg_write(UC_ARM64_REG_V11,  istate['v11'])
    mu.reg_write(UC_ARM64_REG_V12,  istate['v12'])
    mu.reg_write(UC_ARM64_REG_V13,  istate['v13'])
    mu.reg_write(UC_ARM64_REG_V14,  istate['v14'])
    mu.reg_write(UC_ARM64_REG_V15,  istate['v15'])
    mu.reg_write(UC_ARM64_REG_V16,  istate['v16'])
    mu.reg_write(UC_ARM64_REG_V17,  istate['v17'])
    mu.reg_write(UC_ARM64_REG_V18,  istate['v18'])
    mu.reg_write(UC_ARM64_REG_V19,  istate['v19'])
    mu.reg_write(UC_ARM64_REG_V20,  istate['v20'])
    mu.reg_write(UC_ARM64_REG_V21,  istate['v21'])
    mu.reg_write(UC_ARM64_REG_V22,  istate['v22'])
    mu.reg_write(UC_ARM64_REG_V23,  istate['v23'])
    mu.reg_write(UC_ARM64_REG_V24,  istate['v24'])
    mu.reg_write(UC_ARM64_REG_V25,  istate['v25'])
    mu.reg_write(UC_ARM64_REG_V26,  istate['v26'])
    mu.reg_write(UC_ARM64_REG_V27,  istate['v27'])
    mu.reg_write(UC_ARM64_REG_V28,  istate['v28'])
    mu.reg_write(UC_ARM64_REG_V29,  istate['v29'])
    mu.reg_write(UC_ARM64_REG_V30,  istate['v30'])
    mu.reg_write(UC_ARM64_REG_V31,  istate['v31'])
    mu.reg_write(UC_ARM64_REG_PC,   istate['pc'])
    mu.reg_write(UC_ARM64_REG_SP,   istate['sp'])
    mu.reg_write(UC_ARM64_REG_NZCV, istate['n'] << 31 | istate['z'] << 30 | istate['c'] << 29 | istate['v'] << 28)

    # emulate code in infinite time & unlimited instructions
    mu.emu_start(istate['pc'], istate['pc'] + len(opcode))

    ostate = {
        "stack": mu.mem_read(STACK, 0x100),
        "heap":  mu.mem_read(HEAP, 0x100),
        "x0":    mu.reg_read(UC_ARM64_REG_X0),
        "x1":    mu.reg_read(UC_ARM64_REG_X1),
        "x2":    mu.reg_read(UC_ARM64_REG_X2),
        "x3":    mu.reg_read(UC_ARM64_REG_X3),
        "x4":    mu.reg_read(UC_ARM64_REG_X4),
        "x5":    mu.reg_read(UC_ARM64_REG_X5),
        "x6":    mu.reg_read(UC_ARM64_REG_X6),
        "x7":    mu.reg_read(UC_ARM64_REG_X7),
        "x8":    mu.reg_read(UC_ARM64_REG_X8),
        "x9":    mu.reg_read(UC_ARM64_REG_X9),
        "x10":   mu.reg_read(UC_ARM64_REG_X10),
        "x11":   mu.reg_read(UC_ARM64_REG_X11),
        "x12":   mu.reg_read(UC_ARM64_REG_X12),
        "x13":   mu.reg_read(UC_ARM64_REG_X13),
        "x14":   mu.reg_read(UC_ARM64_REG_X14),
        "x15":   mu.reg_read(UC_ARM64_REG_X15),
        "x16":   mu.reg_read(UC_ARM64_REG_X16),
        "x17":   mu.reg_read(UC_ARM64_REG_X17),
        "x18":   mu.reg_read(UC_ARM64_REG_X18),
        "x19":   mu.reg_read(UC_ARM64_REG_X19),
        "x20":   mu.reg_read(UC_ARM64_REG_X20),
        "x21":   mu.reg_read(UC_ARM64_REG_X21),
        "x22":   mu.reg_read(UC_ARM64_REG_X22),
        "x23":   mu.reg_read(UC_ARM64_REG_X23),
        "x24":   mu.reg_read(UC_ARM64_REG_X24),
        "x25":   mu.reg_read(UC_ARM64_REG_X25),
        "x26":   mu.reg_read(UC_ARM64_REG_X26),
        "x27":   mu.reg_read(UC_ARM64_REG_X27),
        "x28":   mu.reg_read(UC_ARM64_REG_X28),
        "x29":   mu.reg_read(UC_ARM64_REG_X29),
        "x30":   mu.reg_read(UC_ARM64_REG_X30),
        "v0":    mu.reg_read(UC_ARM64_REG_V0),
        "v1":    mu.reg_read(UC_ARM64_REG_V1),
        "v2":    mu.reg_read(UC_ARM64_REG_V2),
        "v3":    mu.reg_read(UC_ARM64_REG_V3),
        "v4":    mu.reg_read(UC_ARM64_REG_V4),
        "v5":    mu.reg_read(UC_ARM64_REG_V5),
        "v6":    mu.reg_read(UC_ARM64_REG_V6),
        "v7":    mu.reg_read(UC_ARM64_REG_V7),
        "v8":    mu.reg_read(UC_ARM64_REG_V8),
        "v9":    mu.reg_read(UC_ARM64_REG_V9),
        "v10":   mu.reg_read(UC_ARM64_REG_V10),
        "v11":   mu.reg_read(UC_ARM64_REG_V11),
        "v12":   mu.reg_read(UC_ARM64_REG_V12),
        "v13":   mu.reg_read(UC_ARM64_REG_V13),
        "v14":   mu.reg_read(UC_ARM64_REG_V14),
        "v15":   mu.reg_read(UC_ARM64_REG_V15),
        "v16":   mu.reg_read(UC_ARM64_REG_V16),
        "v17":   mu.reg_read(UC_ARM64_REG_V17),
        "v18":   mu.reg_read(UC_ARM64_REG_V18),
        "v19":   mu.reg_read(UC_ARM64_REG_V19),
        "v20":   mu.reg_read(UC_ARM64_REG_V20),
        "v21":   mu.reg_read(UC_ARM64_REG_V21),
        "v22":   mu.reg_read(UC_ARM64_REG_V22),
        "v23":   mu.reg_read(UC_ARM64_REG_V23),
        "v24":   mu.reg_read(UC_ARM64_REG_V24),
        "v25":   mu.reg_read(UC_ARM64_REG_V25),
        "v26":   mu.reg_read(UC_ARM64_REG_V26),
        "v27":   mu.reg_read(UC_ARM64_REG_V27),
        "v28":   mu.reg_read(UC_ARM64_REG_V28),
        "v29":   mu.reg_read(UC_ARM64_REG_V29),
        "v30":   mu.reg_read(UC_ARM64_REG_V30),
        "v31":   mu.reg_read(UC_ARM64_REG_V31),
        "pc":    mu.reg_read(UC_ARM64_REG_PC),
        "sp":    mu.reg_read(UC_ARM64_REG_SP),
        "n":   ((mu.reg_read(UC_ARM64_REG_NZCV) >> 31) & 1),
        "z":   ((mu.reg_read(UC_ARM64_REG_NZCV) >> 30) & 1),
        "c":   ((mu.reg_read(UC_ARM64_REG_NZCV) >> 29) & 1),
        "v":   ((mu.reg_read(UC_ARM64_REG_NZCV) >> 28) & 1),
    }
    return ostate

def emu_with_triton(opcode, istate):
    ctx = TritonContext()
    ctx.setArchitecture(ARCH.AARCH64)

    inst = Instruction(opcode)
    inst.setAddress(istate['pc'])

    ctx.setConcreteMemoryAreaValue(STACK,           bytes(istate['stack']))
    ctx.setConcreteMemoryAreaValue(HEAP,            bytes(istate['heap']))
    ctx.setConcreteRegisterValue(ctx.registers.x0,  istate['x0'])
    ctx.setConcreteRegisterValue(ctx.registers.x1,  istate['x1'])
    ctx.setConcreteRegisterValue(ctx.registers.x2,  istate['x2'])
    ctx.setConcreteRegisterValue(ctx.registers.x3,  istate['x3'])
    ctx.setConcreteRegisterValue(ctx.registers.x4,  istate['x4'])
    ctx.setConcreteRegisterValue(ctx.registers.x5,  istate['x5'])
    ctx.setConcreteRegisterValue(ctx.registers.x6,  istate['x6'])
    ctx.setConcreteRegisterValue(ctx.registers.x7,  istate['x7'])
    ctx.setConcreteRegisterValue(ctx.registers.x8,  istate['x8'])
    ctx.setConcreteRegisterValue(ctx.registers.x9,  istate['x9'])
    ctx.setConcreteRegisterValue(ctx.registers.x10, istate['x10'])
    ctx.setConcreteRegisterValue(ctx.registers.x11, istate['x11'])
    ctx.setConcreteRegisterValue(ctx.registers.x12, istate['x12'])
    ctx.setConcreteRegisterValue(ctx.registers.x13, istate['x13'])
    ctx.setConcreteRegisterValue(ctx.registers.x14, istate['x14'])
    ctx.setConcreteRegisterValue(ctx.registers.x15, istate['x15'])
    ctx.setConcreteRegisterValue(ctx.registers.x16, istate['x16'])
    ctx.setConcreteRegisterValue(ctx.registers.x17, istate['x17'])
    ctx.setConcreteRegisterValue(ctx.registers.x18, istate['x18'])
    ctx.setConcreteRegisterValue(ctx.registers.x19, istate['x19'])
    ctx.setConcreteRegisterValue(ctx.registers.x20, istate['x20'])
    ctx.setConcreteRegisterValue(ctx.registers.x21, istate['x21'])
    ctx.setConcreteRegisterValue(ctx.registers.x22, istate['x22'])
    ctx.setConcreteRegisterValue(ctx.registers.x23, istate['x23'])
    ctx.setConcreteRegisterValue(ctx.registers.x24, istate['x24'])
    ctx.setConcreteRegisterValue(ctx.registers.x25, istate['x25'])
    ctx.setConcreteRegisterValue(ctx.registers.x26, istate['x26'])
    ctx.setConcreteRegisterValue(ctx.registers.x27, istate['x27'])
    ctx.setConcreteRegisterValue(ctx.registers.x28, istate['x28'])
    ctx.setConcreteRegisterValue(ctx.registers.x29, istate['x29'])
    ctx.setConcreteRegisterValue(ctx.registers.x30, istate['x30'])
    ctx.setConcreteRegisterValue(ctx.registers.v0,  istate['v0'])
    ctx.setConcreteRegisterValue(ctx.registers.v1,  istate['v1'])
    ctx.setConcreteRegisterValue(ctx.registers.v2,  istate['v2'])
    ctx.setConcreteRegisterValue(ctx.registers.v3,  istate['v3'])
    ctx.setConcreteRegisterValue(ctx.registers.v4,  istate['v4'])
    ctx.setConcreteRegisterValue(ctx.registers.v5,  istate['v5'])
    ctx.setConcreteRegisterValue(ctx.registers.v6,  istate['v6'])
    ctx.setConcreteRegisterValue(ctx.registers.v7,  istate['v7'])
    ctx.setConcreteRegisterValue(ctx.registers.v8,  istate['v8'])
    ctx.setConcreteRegisterValue(ctx.registers.v9,  istate['v9'])
    ctx.setConcreteRegisterValue(ctx.registers.v10, istate['v10'])
    ctx.setConcreteRegisterValue(ctx.registers.v11, istate['v11'])
    ctx.setConcreteRegisterValue(ctx.registers.v12, istate['v12'])
    ctx.setConcreteRegisterValue(ctx.registers.v13, istate['v13'])
    ctx.setConcreteRegisterValue(ctx.registers.v14, istate['v14'])
    ctx.setConcreteRegisterValue(ctx.registers.v15, istate['v15'])
    ctx.setConcreteRegisterValue(ctx.registers.v16, istate['v16'])
    ctx.setConcreteRegisterValue(ctx.registers.v17, istate['v17'])
    ctx.setConcreteRegisterValue(ctx.registers.v18, istate['v18'])
    ctx.setConcreteRegisterValue(ctx.registers.v19, istate['v19'])
    ctx.setConcreteRegisterValue(ctx.registers.v20, istate['v20'])
    ctx.setConcreteRegisterValue(ctx.registers.v21, istate['v21'])
    ctx.setConcreteRegisterValue(ctx.registers.v22, istate['v22'])
    ctx.setConcreteRegisterValue(ctx.registers.v23, istate['v23'])
    ctx.setConcreteRegisterValue(ctx.registers.v24, istate['v24'])
    ctx.setConcreteRegisterValue(ctx.registers.v25, istate['v25'])
    ctx.setConcreteRegisterValue(ctx.registers.v26, istate['v26'])
    ctx.setConcreteRegisterValue(ctx.registers.v27, istate['v27'])
    ctx.setConcreteRegisterValue(ctx.registers.v28, istate['v28'])
    ctx.setConcreteRegisterValue(ctx.registers.v29, istate['v29'])
    ctx.setConcreteRegisterValue(ctx.registers.v30, istate['v30'])
    ctx.setConcreteRegisterValue(ctx.registers.v31, istate['v31'])
    ctx.setConcreteRegisterValue(ctx.registers.pc,  istate['pc'])
    ctx.setConcreteRegisterValue(ctx.registers.sp,  istate['sp'])
    ctx.setConcreteRegisterValue(ctx.registers.n,   istate['n'])
    ctx.setConcreteRegisterValue(ctx.registers.z,   istate['z'])
    ctx.setConcreteRegisterValue(ctx.registers.c,   istate['c'])
    ctx.setConcreteRegisterValue(ctx.registers.v,   istate['v'])

    ctx.processing(inst)

    #print
    #print inst
    #for x in inst.getSymbolicExpressions():
    #    print x
    #print

    ostate = {
        "stack": ctx.getConcreteMemoryAreaValue(STACK, 0x100),
        "heap":  ctx.getConcreteMemoryAreaValue(HEAP, 0x100),
        "x0":    ctx.getSymbolicRegisterValue(ctx.registers.x0),
        "x1":    ctx.getSymbolicRegisterValue(ctx.registers.x1),
        "x2":    ctx.getSymbolicRegisterValue(ctx.registers.x2),
        "x3":    ctx.getSymbolicRegisterValue(ctx.registers.x3),
        "x4":    ctx.getSymbolicRegisterValue(ctx.registers.x4),
        "x5":    ctx.getSymbolicRegisterValue(ctx.registers.x5),
        "x6":    ctx.getSymbolicRegisterValue(ctx.registers.x6),
        "x7":    ctx.getSymbolicRegisterValue(ctx.registers.x7),
        "x8":    ctx.getSymbolicRegisterValue(ctx.registers.x8),
        "x9":    ctx.getSymbolicRegisterValue(ctx.registers.x9),
        "x10":   ctx.getSymbolicRegisterValue(ctx.registers.x10),
        "x11":   ctx.getSymbolicRegisterValue(ctx.registers.x11),
        "x12":   ctx.getSymbolicRegisterValue(ctx.registers.x12),
        "x13":   ctx.getSymbolicRegisterValue(ctx.registers.x13),
        "x14":   ctx.getSymbolicRegisterValue(ctx.registers.x14),
        "x15":   ctx.getSymbolicRegisterValue(ctx.registers.x15),
        "x16":   ctx.getSymbolicRegisterValue(ctx.registers.x16),
        "x17":   ctx.getSymbolicRegisterValue(ctx.registers.x17),
        "x18":   ctx.getSymbolicRegisterValue(ctx.registers.x18),
        "x19":   ctx.getSymbolicRegisterValue(ctx.registers.x19),
        "x20":   ctx.getSymbolicRegisterValue(ctx.registers.x20),
        "x21":   ctx.getSymbolicRegisterValue(ctx.registers.x21),
        "x22":   ctx.getSymbolicRegisterValue(ctx.registers.x22),
        "x23":   ctx.getSymbolicRegisterValue(ctx.registers.x23),
        "x24":   ctx.getSymbolicRegisterValue(ctx.registers.x24),
        "x25":   ctx.getSymbolicRegisterValue(ctx.registers.x25),
        "x26":   ctx.getSymbolicRegisterValue(ctx.registers.x26),
        "x27":   ctx.getSymbolicRegisterValue(ctx.registers.x27),
        "x28":   ctx.getSymbolicRegisterValue(ctx.registers.x28),
        "x29":   ctx.getSymbolicRegisterValue(ctx.registers.x29),
        "x30":   ctx.getSymbolicRegisterValue(ctx.registers.x30),
        "v0":    ctx.getSymbolicRegisterValue(ctx.registers.v0),
        "v1":    ctx.getSymbolicRegisterValue(ctx.registers.v1),
        "v2":    ctx.getSymbolicRegisterValue(ctx.registers.v2),
        "v3":    ctx.getSymbolicRegisterValue(ctx.registers.v3),
        "v4":    ctx.getSymbolicRegisterValue(ctx.registers.v4),
        "v5":    ctx.getSymbolicRegisterValue(ctx.registers.v5),
        "v6":    ctx.getSymbolicRegisterValue(ctx.registers.v6),
        "v7":    ctx.getSymbolicRegisterValue(ctx.registers.v7),
        "v8":    ctx.getSymbolicRegisterValue(ctx.registers.v8),
        "v9":    ctx.getSymbolicRegisterValue(ctx.registers.v9),
        "v10":   ctx.getSymbolicRegisterValue(ctx.registers.v10),
        "v11":   ctx.getSymbolicRegisterValue(ctx.registers.v11),
        "v12":   ctx.getSymbolicRegisterValue(ctx.registers.v12),
        "v13":   ctx.getSymbolicRegisterValue(ctx.registers.v13),
        "v14":   ctx.getSymbolicRegisterValue(ctx.registers.v14),
        "v15":   ctx.getSymbolicRegisterValue(ctx.registers.v15),
        "v16":   ctx.getSymbolicRegisterValue(ctx.registers.v16),
        "v17":   ctx.getSymbolicRegisterValue(ctx.registers.v17),
        "v18":   ctx.getSymbolicRegisterValue(ctx.registers.v18),
        "v19":   ctx.getSymbolicRegisterValue(ctx.registers.v19),
        "v20":   ctx.getSymbolicRegisterValue(ctx.registers.v20),
        "v21":   ctx.getSymbolicRegisterValue(ctx.registers.v21),
        "v22":   ctx.getSymbolicRegisterValue(ctx.registers.v22),
        "v23":   ctx.getSymbolicRegisterValue(ctx.registers.v23),
        "v24":   ctx.getSymbolicRegisterValue(ctx.registers.v24),
        "v25":   ctx.getSymbolicRegisterValue(ctx.registers.v25),
        "v26":   ctx.getSymbolicRegisterValue(ctx.registers.v26),
        "v27":   ctx.getSymbolicRegisterValue(ctx.registers.v27),
        "v28":   ctx.getSymbolicRegisterValue(ctx.registers.v28),
        "v29":   ctx.getSymbolicRegisterValue(ctx.registers.v29),
        "v30":   ctx.getSymbolicRegisterValue(ctx.registers.v30),
        "v31":   ctx.getSymbolicRegisterValue(ctx.registers.v31),
        "pc":    ctx.getSymbolicRegisterValue(ctx.registers.pc),
        "sp":    ctx.getSymbolicRegisterValue(ctx.registers.sp),
        "n":     ctx.getSymbolicRegisterValue(ctx.registers.n),
        "z":     ctx.getSymbolicRegisterValue(ctx.registers.z),
        "c":     ctx.getSymbolicRegisterValue(ctx.registers.c),
        "v":     ctx.getSymbolicRegisterValue(ctx.registers.v),
    }
    return ostate


def diff_state(state1, state2):
    for k, v in list(state1.items()):
        if (k == 'heap' or k == 'stack') and v != state2[k]:
            print('\t%s: (UC) != (TT)' %(k))
        elif not (k == 'heap' or k == 'stack') and v != state2[k]:
            print('\t%s: %#x (UC) != %#x (TT)' %(k, v, state2[k]))
    return


if __name__ == '__main__':
    # initial state
    state = {
        "stack": bytearray(b"".join([pack('B', 255 - i) for i in range(256)])),
        "heap":  bytearray(b"".join([pack('B', i) for i in range(256)])),
        "x0":    0,
        "x1":    0,
        "x2":    0,
        "x3":    0,
        "x4":    0,
        "x5":    0,
        "x6":    0,
        "x7":    0,
        "x8":    0,
        "x9":    0,
        "x10":   0,
        "x11":   0,
        "x12":   0,
        "x13":   0,
        "x14":   0,
        "x15":   0,
        "x16":   0,
        "x17":   0,
        "x18":   0,
        "x19":   0,
        "x20":   0,
        "x21":   0,
        "x22":   0,
        "x23":   0,
        "x24":   0,
        "x25":   0,
        "x26":   0,
        "x27":   0,
        "x28":   0,
        "x29":   0,
        "x30":   0,
        "v0":    0x00112233445566778899aabbccddeeff,
        "v1":    0xffeeddccbbaa99887766554433221100,
        "v2":    0xfefedcdc5656787889892692dfeccaa0,
        "v3":    0x1234567890987654321bcdffccddee01,
        "v4":    0,
        "v5":    0,
        "v6":    0,
        "v7":    0,
        "v8":    0,
        "v9":    0,
        "v10":   0,
        "v11":   0,
        "v12":   0,
        "v13":   0,
        "v14":   0,
        "v15":   0,
        "v16":   0,
        "v17":   0,
        "v18":   0,
        "v19":   0,
        "v20":   0,
        "v21":   0,
        "v22":   0,
        "v23":   0,
        "v24":   0,
        "v25":   0,
        "v26":   0,
        "v27":   0,
        "v28":   0,
        "v29":   0,
        "v30":   0,
        "v31":   0,
        "pc":    ADDR,
        "sp":    STACK,
        "n":     0,
        "z":     0,
        "c":     0,
        "v":     0,
    }

    for opcode, disassembly in CODE:
        try:
            uc_state = emu_with_unicorn(opcode, state)
            tt_state = emu_with_triton(opcode, state)
        except Exception as e:
            print('[KO] %s' %(disassembly))
            print('\t%s' %(e))
            sys.exit(-1)

        if uc_state != tt_state:
            print('[KO] %s' %(disassembly))
            diff_state(uc_state, tt_state)
            sys.exit(-1)

        print('[OK] %s' %(disassembly))
        state = tt_state

    sys.exit(0)
