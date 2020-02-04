{{- define "opwen.environment.shared" -}}
        - name: LOKOLE_LOG_LEVEL
          value: {{.Values.logging.level}}
        - name: LOKOLE_CLIENT_AZURE_STORAGE_KEY
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_CLIENT_AZURE_STORAGE_KEY
        - name: LOKOLE_CLIENT_AZURE_STORAGE_NAME
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_CLIENT_AZURE_STORAGE_NAME
        - name: LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_AZURE_BLOBS_KEY
        - name: LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME
        - name: LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_AZURE_TABLES_KEY
        - name: LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME
        - name: LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_APPINSIGHTS_KEY
        - name: LOKOLE_CLOUDFLARE_USER
          valueFrom:
            secretKeyRef:
              name: cloudflare
              key: LOKOLE_CLOUDFLARE_USER
        - name: LOKOLE_CLOUDFLARE_KEY
          valueFrom:
            secretKeyRef:
              name: cloudflare
              key: LOKOLE_CLOUDFLARE_KEY
        - name: LOKOLE_SENDGRID_KEY
          valueFrom:
            secretKeyRef:
              name: sendgrid
              key: LOKOLE_SENDGRID_KEY
        - name: LOKOLE_QUEUE_BROKER_SCHEME
          value: azureservicebus
        - name: LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_QUEUES_SAS_NAME
        - name: LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_QUEUES_SAS_KEY
        - name: LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE
          valueFrom:
            secretKeyRef:
              name: azure
              key: LOKOLE_EMAIL_SERVER_QUEUES_NAMESPACE
{{- end -}}
