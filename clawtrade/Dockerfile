FROM golang:1.24-alpine AS build
WORKDIR /src
RUN apk add --no-cache git ca-certificates
RUN git clone --depth 1 --branch master https://github.com/Paparusi/Clawtrade.git .
RUN go build -trimpath -ldflags='-s -w' -o /out/clawtrade ./cmd/clawtrade

FROM alpine:3.22
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=build /out/clawtrade /usr/local/bin/clawtrade
COPY config.yaml /app/config.yaml
RUN mkdir -p /app/data
EXPOSE 8899
ENV CLAWTRADE_CONFIG=/app/config.yaml
CMD ["/usr/local/bin/clawtrade", "serve"]
