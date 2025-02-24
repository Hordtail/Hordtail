import boto3
import json

ec2_client = boto3.client('ec2')
route53_client = boto3.client('route53')

HOSTED_ZONE_ID = "Z06113313M7JJFJ9M7HM8"  # Reemplazar con el Hosted Zone de Route 53

def lambda_handler(event, context):
    try:
        instance_id = event['detail']['instance-id']
        print(f"Instance ID: {instance_id}")
        
        # Obtener tags de la instancia
        tags = ec2_client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [instance_id]}])
        print(f"Tags: {tags}")
        
        dns_names = None
        for tag in tags['Tags']:
            if tag['Key'] == 'DomainName':
                dns_names = tag['Value'].split(',')
                break
                
        if not dns_names:
            print("No DNS_NAMES tag found.")
            return
        
        print(f"DNS Names: {dns_names}")
        
        # Obtener IP de la instancia
        instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])
        print(f"Instance Details: {instance_details}")
        
        ip_address = instance_details['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        if not ip_address:
            print(f"No public IP found for instance {instance_id}")
            return
        
        print(f"Public IP: {ip_address}")
        
        # Crear registros en Route 53
        changes = []
        for name in dns_names:
            record_name = f"{name}.campusdual.mkcampus.com."
            changes.append({
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_name,
                    'Type': 'A',
                    'TTL': 60,  # Consider using a more standard TTL
                    'ResourceRecords': [{'Value': ip_address}]
                }
            })
        
        print(f"Changes: {changes}")
        
        # Realizar la solicitud de cambio de registros
        response = route53_client.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={'Changes': changes}
        )
        
        print(f"DNS records created: {', '.join(dns_names)} -> {ip_address}")
        print(f"Route 53 Response: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")
