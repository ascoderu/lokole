#!/usr/bin/env bash

set -euo pipefail
out_dir="$(dirname "$0")/../files/end_to_end/test.out"
mkdir -p "${out_dir}"

num_emails_actual="$(wc -l "${out_dir}/emails.jsonl" | cut -d' ' -f1)"
num_emails_expected=1

if [[ "${num_emails_actual}" -ne "${num_emails_expected}" ]]; then
  echo "Got ${num_emails_actual} but expected ${num_emails_expected}" >&2
  exit 1
fi
