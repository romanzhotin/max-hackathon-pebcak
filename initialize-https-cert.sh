docker compose --profile acme up -d certbot nginx-acme

sleep 5

docker compose --profile acme logs -n 10 certbot nginx-acme

docker compose --profile acme down certbot nginx-acme