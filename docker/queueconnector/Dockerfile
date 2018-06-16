FROM microsoft/dotnet:2.0-sdk-stretch AS builder

WORKDIR /app
COPY opwen_queue_connector/*.csproj ./
RUN dotnet restore
COPY opwen_queue_connector/*.cs ./
RUN dotnet publish -c Release -o out

FROM microsoft/dotnet:2.0-runtime-stretch

WORKDIR /app
ADD docker/docker-entrypoint.sh /docker-entrypoint.sh
COPY --from=builder /app/out ./

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["dotnet", "queueconnector.dll"]
