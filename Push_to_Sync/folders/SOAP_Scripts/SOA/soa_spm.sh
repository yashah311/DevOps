#!/bin/bash

platformw component spm status aabc-domain

./soa_spm_flush_SOA1.sh SOA1
./soa_spm_flush_SOA2.sh SOA2

platformw component spm status aabc-domain

