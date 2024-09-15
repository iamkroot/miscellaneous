#!/usr/bin/env bash

# use by running `source vm_control.sh`, this will make the functions below available to be called from CLI.
# for now, you need to manually edit this file to change the filter in vmids

# helpers to power on the servers, get status
# requires curlie (make curl requests), jq (parse json), parallel (parallelize some jobs), and rbw (to store/fetch pwds)

VS_SESS=""
API_HOST="https://vc8-csvm.cs.illinois.edu/api"

alias parcall='parallel -j4 curlie -k -H vmware-api-session-id:$VS_SESS'

function getsesstok() {
	# check if the current token is valid
	resp=$(curlie get --connect-timeout 1 -s -w "%{http_code}" -o /dev/null -k -H vmware-api-session-id:$VS_SESS "${API_HOST}/session")
	if [ $? -ne 0 ]; then
		echo "Connect error. r u VPN?" >&2
		return 1
	fi
	[[ resp -eq "200" ]] && return 0;
	read username pwd < <(echo $(rbw get UIUC --raw | jq -r '.data.username, .data.password'))
	tok=$(echo -n $username:$pwd | python -m base64 -e)
	resp=$(curlie -k post "${API_HOST}/session" Authorization:"Basic ${tok}")
	err=$(echo $resp | jq ".error_type?")
	if [ -n "$err" ]; then
		echo "Auth error. Check username/pwd" >&2
		echo "$resp" | jq >&2
		return 1
	fi
	export VS_SESS=$(echo $resp | jq -r)
}

function vmids() {
	getsesstok || return 1;
	curlie -k -H vmware-api-session-id:$VS_SESS "${API_HOST}/vcenter/vm" | jq -r '.[] | (select(.name | test("cs525")).vm)'
}

function start_vms() {
	getsesstok || return 1;
	vmids | parcall post "${API_HOST}/vcenter/vm/{}/power" action==start | jq
}

function stop_vms() {
	getsesstok || return 1;
	vmids | parcall post "${API_HOST}/vcenter/vm/{}/power" action==stop | jq
}

function vm_status() {
	getsesstok || return 1;
	vmids | parcall get "${API_HOST}/vcenter/vm/{}/power" | jq
}
