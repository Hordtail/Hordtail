import boto3
import json

ec2_client = boto3.client('ec2')
route53_client = boto3.client('route53')

HOSTED_ZONE_ID = "Z06113313M7JJFJ9M7HM8"  # Reemplazar con el Hosted Zone de Route 53

def lambda_handler(event, context):
    try:
        instance_id = event['detail']['instance-id']
        
        # Obtener tags de la instancia
        tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [instance_id]}])
        dns_names = None
        
        for tag in tags['Tags']:
            if tag['Key'] == 'DOMAIN_NAME_B':
                dns_names = tag['Value'].split(',')
                break
                
        if not dns_names:
            print("No DNS_NAMES tag found.")
            return
        
        import os

        domain_name = os.environ['DOMAIN_NAME_B']  # Acceder a la variable de entorno
        print(f"El nombre de dominio es: {domain_name}")
        
        # Obtener IP de la instancia
        instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])
        ip_address = instance_details['Reservations'][0]['Instances'][0]['PublicIpAddress']
        
        # Crear registros en Route 53
        changes = []
        for name in dns_names:
            record_name = f"{name}.campusdual.mkcampus.com."
            changes.append({
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'A',
                    'TTL': 80,
                    'ResourceRecords': [{'Value': ip_address}]
                }
            })
        
        route53_client.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={'Changes': changes}
        )
        
        print(f"DNS records created: {', '.join(dns_names)} -> {ip_address}")
    except Exception as e:
        print(f"Error: {str(e)}")