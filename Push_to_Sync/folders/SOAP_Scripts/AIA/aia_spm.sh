#!/bin/bash

platformw component spm status o2c-domain

./aia_spm_flush_SOA1.sh SOA1
./aia_spm_flush_SOA2.sh SOA2

platformw component spm status o2c-domain



