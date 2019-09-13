FROM alpine

RUN apk update && apk add bash jq curl openssl

ADD test_policies.sh /root/run.sh
RUN chmod +x /root/run.sh

CMD ["bash", "/root/run.sh" ]
