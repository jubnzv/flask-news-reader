#!/usr/bin/env bash
# This is required to compile required dependencies on a cheap 1Gb RAM digital
# ocean droplet.
SWAP=/tmpswap
dd if=/dev/zero of="$SWAP" bs=1024 count=1M
chmod 0600 $SWAP
mkswap $SWAP
swapon $SWAP
