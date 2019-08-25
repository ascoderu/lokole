#!/usr/bin/env bash
set -euo pipefail

./tests/integration/wait.sh
./tests/integration/0-register-client.sh
./tests/integration/1-client-uploads-emails.sh && sleep 10s
./tests/integration/2-receive-email-for-client.sh && sleep 10s
./tests/integration/3-client-downloads-emails.sh
./tests/integration/assert.sh
rm -rf tests/files/end_to_end/test.out
