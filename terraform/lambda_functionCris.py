import json
import boto3
import logging

ec2_client = boto3.client('ec2')
route53_client = boto3.client('route53')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        instance_id = event.get('detail', {}).get('instance-id')
        if not instance_id:
            raise ValueError("No se ha encontrado el ID de la instancia en el evento.")
        
        logger.info(f"ID de la instancia: {instance_id}")
        
        tags = get_instance_tags(instance_id)
        dns_names = extract_dns_names(tags)

        if not dns_names:
            raise ValueError("No se ha encontrado el tag 'DNS_NAMES' en los tags de la instancia.")

        create_dns_records(dns_names, instance_id)

        return {
            'statusCode': 200,
            'body': json.dumps('Registros DNS creados correctamente.')
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

def get_instance_tags(instance_id):
    response = ec2_client.describe_tags(
        Filters=[{'Name': 'resource-id', 'Values': [instance_id]}]
    )
    return response.get('Tags', [])

def extract_dns_names(tags):
    dns_names = None
    for tag in tags:
        if tag['Key'] == 'DomainName':
            dns_names = tag['Value']
            break
    return dns_names.split(',') if dns_names else None

def get_instance_public_ip(instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    
    reservations = response.get('Reservations', [])
    if not reservations:
        return None

    instances = reservations[0].get('Instances', [])
    if not instances:
        return None

    return instances[0].get('PublicIpAddress')

def create_dns_records(dns_names, instance_id):
    hosted_zone_id = '/hostedzone/Z06113313M7JJFJ9M7HM8' # aws route53 list-hosted-zones
    domain_suffix = "campusdual.mkcampus.com" 

    # Obtener la IP pública de la instancia EC2
    public_ip = get_instance_public_ip(instance_id)
    if not public_ip:
        raise ValueError(f"No se pudo obtener la IP pública de la instancia {instance_id}.")

    logger.info(f"IP pública obtenida: {public_ip}")

    change_batch = {'Changes': []}
    for dns_name in dns_names:
        dns_name = dns_name.strip() 

        if not dns_name.endswith(domain_suffix):
            dns_name = f"{dns_name}.{domain_suffix}"

        change_batch['Changes'].append({
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': dns_name, 
                'Type': 'A',
                'TTL': 60,
                'ResourceRecords': [{'Value': public_ip}]
            }
        })

    response = route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch=change_batch
    )

    logger.info(f"Respuesta de Route 53: {json.dumps(response)}")