#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GTX Extractor
# Version v5.0
# Copyright © 2014 Treeki, 2015-2017 AboodXD

# This file is part of GTX Extractor.

# GTX Extractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# GTX Extractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""gtx_extract.py: Decode GTX images."""

import os
import struct
import sys
import time

try:
    import addrlib_cy as addrlib
except ImportError:
    import addrlib

__author__ = "AboodXD"
__copyright__ = "Copyright 2014 Treeki, 2015-2017 AboodXD"
__credits__ = ["AboodXD", "Treeki", "AddrLib", "Exzap"]

formats = {0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
           0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
           0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
           0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
           0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
           0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
           0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
           0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
           0x00000007: 'GX2_SURFACE_FORMAT_TC_R8_G8_UNORM',
           0x00000002: 'GX2_SURFACE_FORMAT_TC_R4_G4_UNORM',
           0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
           0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
           0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
           0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
           0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
           0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB',
           0x00000034: 'GX2_SURFACE_FORMAT_T_BC4_UNORM',
           0x00000234: 'GX2_SURFACE_FORMAT_T_BC4_SNORM',
           0x00000035: 'GX2_SURFACE_FORMAT_T_BC5_UNORM',
           0x00000235: 'GX2_SURFACE_FORMAT_T_BC5_SNORM'
           }

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x234, 0x35, 0x235]


# ----------\/-Start of GTX Extracting section-\/------------- #
class GFDData:
    pass


class GFDHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.majorVersion,
         self.minorVersion,
         self.gpuVersion,
         self.alignMode,
         self.reserved1,
         self.reserved2) = self.unpack_from(data, pos)


class GFDBlockHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.majorVersion,
         self.minorVersion,
         self.type_,
         self.dataSize,
         self.id,
         self.typeIdx) = self.unpack_from(data, pos)


class GX2Surface(struct.Struct):
    def __init__(self):
        super().__init__('>16I')

    def data(self, data, pos):
        (self.dim,
         self.width,
         self.height,
         self.depth,
         self.numMips,
         self.format_,
         self.aa,
         self.use,
         self.imageSize,
         self.imagePtr,
         self.mipSize,
         self.mipPtr,
         self.tileMode,
         self.swizzle,
         self.alignment,
         self.pitch) = self.unpack_from(data, pos)


def swapRB(bgra):
    return bytes((bgra[2], bgra[1], bgra[0], bgra[3]))


def readGFD(f):
    gfd = GFDData()

    pos = 0

    header = GFDHeader()
    header.data(f, pos)

    if header.magic != b'Gfx2':
        raise ValueError("Invalid file header!")

    pos += header.size

    blockB = False
    blockC = False

    images = 0
    imgInfo = 0

    gfd.dim = []
    gfd.width = []
    gfd.height = []
    gfd.depth = []
    gfd.numMips = []
    gfd.format = []
    gfd.aa = []
    gfd.use = []
    gfd.imageSize = []
    gfd.imagePtr = []
    gfd.mipSize = []
    gfd.mipPtr = []
    gfd.tileMode = []
    gfd.swizzle = []
    gfd.alignment = []
    gfd.pitch = []
    gfd.compSel = []
    gfd.surfOut = []
    gfd.realSize = []

    gfd.dataSize = []
    gfd.data = []

    while pos < len(f):  # Loop through the entire file, stop if reached the end of the file.
        block = GFDBlockHeader()
        block.data(f, pos)

        if block.magic != b'BLK{':
            raise ValueError("Invalid block header!")

        pos += block.size

        if block.type_ == 0x0B:
            imgInfo += 1
            blockB = True

            surface = GX2Surface()
            surface.data(f, pos)

            pos += surface.size
            pos += 68

            compSel = []
            for i in range(4):
                compSel.append(f[pos + i])

            pos += 24

            if surface.format_ in BCn_formats:
                width = surface.width // 4
                height = surface.height // 4
            else:
                width = surface.width
                height = surface.height

            surfOut = addrlib.getSurfaceInfo(surface.format_, width, height, surface.depth, surface.dim, surface.tileMode, surface.aa, 0)

            gfd.dim.append(surface.dim)
            gfd.width.append(surface.width)
            gfd.height.append(surface.height)
            gfd.depth.append(surface.depth)
            gfd.numMips.append(surface.numMips)
            gfd.format.append(surface.format_)
            gfd.aa.append(surface.aa)
            gfd.use.append(surface.use)
            gfd.imageSize.append(surface.imageSize)
            gfd.imagePtr.append(surface.imagePtr)
            gfd.mipSize.append(surface.mipSize)
            gfd.mipPtr.append(surface.mipPtr)
            gfd.tileMode.append(surface.tileMode)
            gfd.swizzle.append(surface.swizzle)
            gfd.alignment.append(surface.alignment)
            gfd.pitch.append(surfOut.pitch)
            gfd.compSel.append(compSel)
            gfd.surfOut.append(surfOut)
            if surface.format_ in BCn_formats:
                gfd.realSize.append(((surface.width + 3) >> 2) * ((surface.height + 3) >> 2) * (
                    addrlib.surfaceGetBitsPerPixel(surface.format_) // 8))
            else:
                gfd.realSize.append(
                    surface.width * surface.height * (addrlib.surfaceGetBitsPerPixel(surface.format_) // 8))

        elif block.type_ == 0x0C:
            images += 1
            blockC = True

            gfd.dataSize.append(block.dataSize)
            gfd.data.append(f[pos:pos + block.dataSize])
            pos += block.dataSize

        else:
            pos += block.dataSize

    if images != imgInfo:
        print("")
        print("Whoops, fail! XD")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if blockB:
        if not blockC:
            print("")
            print("Image info was found but no Image data was found.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)
    if not blockB:
        if not blockC:
            print("")
            print("No Image was found in this file.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)
        elif blockC:
            print("")
            print("Image data was found but no Image info was found.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    gfd.numImages = images

    return gfd


def get_deswizzled_data(i, numImages, width, height, depth, dim, format_, aa, tileMode, swizzle_, pitch, compSel, data, size, surfOut):
    if format_ in formats:
        if aa != 0:
            print("")
            print("Unsupported aa!")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', b''
            else:
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

        if format_ == 0x00:
            print("")
            print("Invalid texture format!")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', b''
            else:
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

        else:
            if format_ == 0x1a or format_ == 0x41a:
                format__ = 28
            elif format_ == 0x19:
                format__ = 24
            elif format_ == 0x8:
                format__ = 85
            elif format_ == 0xa:
                format__ = 86
            elif format_ == 0xb:
                format__ = 115
            elif format_ == 0x1:
                format__ = 61
            elif format_ == 0x7:
                format__ = 49
            elif format_ == 0x2:
                format__ = 112
            elif format_ == 0x31 or format_ == 0x431:
                format__ = "BC1"
            elif format_ == 0x32 or format_ == 0x432:
                format__ = "BC2"
            elif format_ == 0x33 or format_ == 0x433:
                format__ = "BC3"
            elif format_ == 0x34:
                format__ = "BC4U"
            elif format_ == 0x234:
                format__ = "BC4S"
            elif format_ == 0x35:
                format__ = "BC5U"
            elif format_ == 0x235:
                format__ = "BC5S"

            if surfOut.depth != 1:
                print("")
                print("Unsupported depth!")
                if i != (numImages - 1):
                    print("Continuing in 5 seconds...")
                    time.sleep(5)
                    return b'', b''
                else:
                    print("Exiting in 5 seconds...")
                    time.sleep(5)
                    sys.exit(1)

            result = addrlib.deswizzle(width, height, surfOut.height, format_, surfOut.tileMode, swizzle_, pitch, surfOut.bpp, data)
            result = result[:size]

            hdr = writeHeader(1, width, height, format__, compSel, size, format_ in BCn_formats)

    else:
        print("")
        print("Unsupported texture format_: " + hex(format_))
        if i != (numImages - 1):
            print("Continuing in 5 seconds...")
            time.sleep(5)
            hdr, result = b'', b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    return hdr, result


def writeGFD(width, height, depth, dim, format_, aa, tileMode, swizzle_, pitch, imageSize, f, f1, surfOut):
    if format_ in formats:
        if aa != 0:
            print("")
            print("Unsupported aa!")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

        if format_ == 0x00:
            print("")
            print("Invalid texture format!")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

        else:
            if format_ not in BCn_formats:
                bpp = struct.unpack("<I", f1[0x14:0x18])[0] // width
                dataSize = bpp * width * height
            else:
                dataSize = struct.unpack("<I", f1[0x14:0x18])[0]

            if not dataSize < imageSize:
                data = f1[0x80:0x80 + imageSize]
            else:
                data = f1[0x80:0x80 + dataSize]
                data += b'\x00' * (imageSize - dataSize)

    else:
        print("")
        print("Unsupported texture format_: " + hex(format_))
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if surfOut.depth != 1:
            print("")
            print("Unsupported depth!")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    swizzled_data = addrlib.swizzle(width, height, surfOut.height, format_, surfOut.tileMode, swizzle_, pitch, surfOut.bpp, data)

    dataSize = len(swizzled_data)

    pos = 0
    header = GFDHeader()
    header.data(f, pos)
    pos += header.size

    while pos < len(f):  # Loop through the entire file.
        block = GFDBlockHeader()
        block.data(f, pos)

        pos += block.size

        if block.type_ == 0x0B:
            offset = pos

            pos += block.dataSize

        elif block.type_ == 0x0C:
            head1 = f[:pos]  # it works :P
            offset1 = pos
            pos += block.dataSize

        else:
            pos += block.dataSize

    head1 = bytearray(head1)
    head1[offset + 0x10:offset + 0x14] = bytes(bytearray.fromhex("00000001"))  # numMips
    head1[offset + 0x78:offset + 0x7C] = bytes(bytearray.fromhex("00000001"))  # numMips, again
    head1[offset + 0x28:offset + 0x2C] = bytes(bytearray.fromhex("00000000"))  # mipSize
    head1[offset + 0x20:offset + 0x24] = int(dataSize).to_bytes(4, 'big')  # imageSize
    head1[offset1 - 0x0C:offset1 - 0x08] = int(dataSize).to_bytes(4, 'big')  # dataSize

    head2 = bytes(bytearray.fromhex("424C4B7B00000020000000010000000000000001000000000000000000000000"))

    return bytes(head1) + bytes(swizzled_data) + head2


# ----------\/-Start of DDS writer section-\/---------- #

# Copyright © 2016-2017 AboodXD

# Supported formats:
#  -RGBA8
#  -RGB10A2
#  -RGB565
#  -RGB5A1
#  -RGBA4
#  -L8
#  -L8A8
#  -L4A4
#  -BC1_UNORM
#  -BC2_UNORM
#  -BC3_UNORM
#  -BC4_UNORM
#  -BC4_SNORM
#  -BC5_UNORM
#  -BC5_SNORM

# Feel free to include this in your own program if you want, just give credits. :)

def writeHeader(num_mipmaps, w, h, format_, compSel, size, compressed):
    hdr = bytearray(128)

    if format_ == 28:  # RGBA8
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x0000ff00
        bmask = 0x00ff0000
        amask = 0xff000000

    elif format_ == 24:  # RGB10A2
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000003ff
        gmask = 0x000ffc00
        bmask = 0x3ff00000
        amask = 0xc0000000

    elif format_ == 85:  # RGB565
        fmtbpp = 2
        has_alpha = 0
        rmask = 0x0000001f
        gmask = 0x000007e0
        bmask = 0x0000f800
        amask = 0x00000000

    elif format_ == 86:  # RGB5A1
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x0000001f
        gmask = 0x000003e0
        bmask = 0x00007c00
        amask = 0x00008000

    elif format_ == 115:  # RGBA4
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x0000000f
        gmask = 0x000000f0
        bmask = 0x00000f00
        amask = 0x0000f000

    elif format_ == 61:  # L8
        fmtbpp = 1
        has_alpha = 0
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x00000000

    elif format_ == 49:  # L8A8
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x0000ff00

    elif format_ == 112:  # L4A4
        fmtbpp = 1
        has_alpha = 1
        rmask = 0x0000000f
        gmask = 0x0000000f
        bmask = 0x0000000f
        amask = 0x000000f0

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002

    caps = 0x00001000

    if num_mipmaps == 0:
        num_mipmaps = 1
    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008

        if fmtbpp == 1 or format_ == 49:  # LUMINANCE
            pflags = 0x00020000

        else:  # RGB
            pflags = 0x00000040

        if has_alpha != 0:
            pflags |= 0x00000001

        size = w * fmtbpp

    else:
        flags |= 0x00080000
        pflags = 0x00000004

        if format_ == "BC1":
            fourcc = b'DXT1'
        elif format_ == "BC2":
            fourcc = b'DXT3'
        elif format_ == "BC3":
            fourcc = b'DXT5'
        elif format_ == "BC4U":
            fourcc = b'BC4U'
        elif format_ == "BC4S":
            fourcc = b'BC4S'
        elif format_ == "BC5U":
            fourcc = b'BC5U'
        elif format_ == "BC5S":
            fourcc = b'BC5S'

    hdr[:4] = b'DDS '
    hdr[4:4 + 4] = 124 .to_bytes(4, 'little')
    hdr[8:8 + 4] = flags.to_bytes(4, 'little')
    hdr[12:12 + 4] = h.to_bytes(4, 'little')
    hdr[16:16 + 4] = w.to_bytes(4, 'little')
    hdr[20:20 + 4] = size.to_bytes(4, 'little')
    hdr[28:28 + 4] = num_mipmaps.to_bytes(4, 'little')
    hdr[76:76 + 4] = 32 .to_bytes(4, 'little')
    hdr[80:80 + 4] = pflags.to_bytes(4, 'little')

    if compressed:
        hdr[84:84 + 4] = fourcc
    else:
        hdr[88:88 + 4] = (fmtbpp << 3).to_bytes(4, 'little')

        if compSel[0] == 1:
            hdr[92:92 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[0] == 2:
            hdr[92:92 + 4] = bmask.to_bytes(4, 'little')
        elif compSel[0] == 3:
            hdr[92:92 + 4] = amask.to_bytes(4, 'little')
        else:
            hdr[92:92 + 4] = rmask.to_bytes(4, 'little')

        if compSel[1] == 0:
            hdr[96:96 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[1] == 2:
            hdr[96:96 + 4] = bmask.to_bytes(4, 'little')
        elif compSel[1] == 3:
            hdr[96:96 + 4] = amask.to_bytes(4, 'little')
        else:
            hdr[96:96 + 4] = gmask.to_bytes(4, 'little')

        if compSel[2] == 0:
            hdr[100:100 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[2] == 1:
            hdr[100:100 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[2] == 3:
            hdr[100:100 + 4] = amask.to_bytes(4, 'little')
        else:
            hdr[100:100 + 4] = bmask.to_bytes(4, 'little')

        if compSel[3] == 0:
            hdr[104:104 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[3] == 1:
            hdr[104:104 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[3] == 2:
            hdr[104:104 + 4] = bmask.to_bytes(4, 'little')
        else:
            hdr[104:104 + 4] = amask.to_bytes(4, 'little')

    hdr[108:108 + 4] = caps.to_bytes(4, 'little')

    return hdr


def main():
    """
    This place is a mess...
    """
    print("GTX Extractor v5.0")
    print("(C) 2014 Treeki, 2015-2017 AboodXD")

    if len(sys.argv) != 2:
        if len(sys.argv) != 3:
            print("")
            print("Usage (If converting from .gtx to .dds, and using source code): python gtx_extract.py input")
            print("Usage (If converting from .gtx to .dds, and using exe): gtx_extract.exe input")
            print(
                "Usage (If converting from .dds to .gtx, and using source code): python gtx_extract.py input(.dds) input(.gtx)")
            print("Usage (If converting from .dds to .gtx, and using exe): gtx_extract.exe input(.dds) input(.gtx)")
            print("")
            print("Supported formats:")
            print(" - GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM")
            print(" - GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB")
            print(" - GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM")
            print(" - GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM")
            print(" - GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM")
            print(" - GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM")
            print(" - GX2_SURFACE_FORMAT_TC_R8_UNORM")
            print(" - GX2_SURFACE_FORMAT_TC_R8_G8_UNORM")
            print(" - GX2_SURFACE_FORMAT_TC_R4_G4_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC1_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC1_SRGB")
            print(" - GX2_SURFACE_FORMAT_T_BC2_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC2_SRGB")
            print(" - GX2_SURFACE_FORMAT_T_BC3_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC3_SRGB")
            print(" - GX2_SURFACE_FORMAT_T_BC4_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC4_SNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC5_UNORM")
            print(" - GX2_SURFACE_FORMAT_T_BC5_SNORM")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    if sys.argv[1].endswith('.gtx'):
        with open(sys.argv[1], "rb") as inf:
            print('Converting: ' + sys.argv[1])
            inb = inf.read()
            inf.close()

    elif sys.argv[1].endswith('.dds'):
        with open(sys.argv[2], "rb") as inf:
            with open(sys.argv[1], "rb") as img:
                print('Converting: ' + sys.argv[1])
                inb = inf.read()
                img1 = img.read()
                inf.close()
                img.close()

    compSel = ["Red", "Green", "Blue", "Alpha", "0", "1"]

    gfd = readGFD(inb)

    for i in range(gfd.numImages):

        print("")
        print("// ----- GX2Surface Info ----- ")
        print("  dim             = " + str(gfd.dim[i]))
        print("  width           = " + str(gfd.width[i]))
        print("  height          = " + str(gfd.height[i]))
        print("  depth           = " + str(gfd.depth[i]))
        print("  numMips         = " + str(gfd.numMips[i]))
        if gfd.format[i] in formats:
            print("  format          = " + formats[gfd.format[i]])
        else:
            print("  format          = " + hex(gfd.format[i]))
        print("  aa              = " + str(gfd.aa[i]))
        print("  use             = " + str(gfd.use[i]))
        print("  imageSize       = " + str(gfd.imageSize[i]))
        print("  mipSize         = " + str(gfd.mipSize[i]))
        print("  tileMode        = " + str(gfd.tileMode[i]))
        print("  swizzle         = " + str(gfd.swizzle[i]) + ", " + hex(gfd.swizzle[i]))
        print("  alignment       = " + str(gfd.alignment[i]))
        print("  pitch           = " + str(gfd.pitch[i]))
        bpp = addrlib.surfaceGetBitsPerPixel(gfd.format[i])
        print("")
        print("  GX2 Component Selector:")
        print("    Channel 1:      " + str(compSel[gfd.compSel[i][0]]))
        print("    Channel 2:      " + str(compSel[gfd.compSel[i][1]]))
        print("    Channel 3:      " + str(compSel[gfd.compSel[i][2]]))
        print("    Channel 4:      " + str(compSel[gfd.compSel[i][3]]))
        print("")
        print("  bits per pixel  = " + str(bpp))
        print("  bytes per pixel = " + str(bpp // 8))
        print("  realSize        = " + str(gfd.realSize[i]))

        name = os.path.splitext(sys.argv[1])[0]

        if sys.argv[1].endswith('.gtx'):
            if gfd.numImages > 1:
                name += str(i)

            hdr, data = get_deswizzled_data(i, gfd.numImages, gfd.width[i], gfd.height[i], gfd.depth[i], gfd.dim[i],
                                            gfd.format[i],gfd.aa[i], gfd.tileMode[i], gfd.swizzle[i], gfd.pitch[i],
                                            gfd.compSel[i], gfd.data[i], gfd.realSize[i], gfd.surfOut[i])

            if data == b'':
                pass
            else:
                output = open(name + '.dds', 'wb+')
                output.write(hdr)
                output.write(data)
                output.close()

        elif sys.argv[1].endswith('.dds'):
            if gfd.numImages > 1:
                print("")
                print("Nope, you still can't do this... :P")
                print("")
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

            data = writeGFD(gfd.width[i], gfd.height[i], gfd.depth[i], gfd.dim[i], gfd.format[i], gfd.aa[i],
                            gfd.tileMode[i], gfd.swizzle[i], gfd.pitch[i], gfd.imageSize[i], inb, img1, gfd.surfOut[i])

            if os.path.isfile(name + ".gtx"):
                # i = 2
                # while os.path.isfile(name + str(i) + ".gtx"):
                #    i += 1
                # output = open(name + str(i) + ".gtx", 'wb+')
                output = open(name + "2.gtx", 'wb+')
            else:
                output = open(name + ".gtx", 'wb+')

            output.write(data)
            output.close()

    print('')
    print('Finished converting: ' + sys.argv[1])


if __name__ == '__main__':
    main()
