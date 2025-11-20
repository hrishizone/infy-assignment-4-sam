
FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html/*

COPY web/ /usr/share/nginx/html/

EXPOSE 80
