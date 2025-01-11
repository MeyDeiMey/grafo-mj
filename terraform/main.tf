# Provider configuration
provider "aws" {
  region = "us-east-1"
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Data source for default VPC
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# IAM role for Systems Manager
resource "aws_iam_role" "ssm_role" {
  name = "graph-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm_profile" {
  name = "graph-ssm-profile"
  role = aws_iam_role.ssm_role.name
}

# Security Group
resource "aws_security_group" "graph_sg" {
  name_prefix = "graph-sg-"
  description = "Security group for graph application"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic"
  }

  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow application traffic"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "graph-security-group"
  }
}

# EC2 Instance
resource "aws_instance" "graph_ec2" {
  ami           = "ami-0e731c8a588258d0d"  # Amazon Linux 2023
  instance_type = "t2.micro"
  subnet_id     = tolist(data.aws_subnets.default.ids)[0]

  vpc_security_group_ids      = [aws_security_group.graph_sg.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.ssm_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    exec > >(tee /var/log/user-data.log) 2>&1

    # Update and install dependencies
    dnf update -y
    dnf install -y python3-pip git nginx amazon-cloudwatch-agent

    # Configure permissions
    usermod -a -G wheel ec2-user
    chown -R ec2-user:ec2-user /home/ec2-user

    # Clone repository
    cd /home/ec2-user
    git clone https://github.com/MeyDeiMey/grafo-mj.git app
    
    # Install Python dependencies
    cd /home/ec2-user/app
    pip3 install -r requirements.txt
    pip3 install gunicorn flask-cors

    # Configure Nginx
    cat > /etc/nginx/conf.d/graphword.conf << 'EOL'
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:5001;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    EOL

    rm -f /etc/nginx/conf.d/default.conf

    # Configure CloudWatch agent
    cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOL'
    {
      "logs": {
        "logs_collected": {
          "files": {
            "collect_list": [
              {
                "file_path": "/var/log/user-data.log",
                "log_group_name": "/graph/user-data",
                "log_stream_name": "{instance_id}"
              },
              {
                "file_path": "/home/ec2-user/app/app.log",
                "log_group_name": "/graph/application",
                "log_stream_name": "{instance_id}"
              }
            ]
          }
        }
      }
    }
    EOL

    # Start CloudWatch agent
    systemctl enable amazon-cloudwatch-agent
    systemctl start amazon-cloudwatch-agent

    # Configure and start services
    systemctl enable nginx
    systemctl start nginx

    # Create systemd service
    cat > /etc/systemd/system/graphapp.service << 'EOL'
    [Unit]
    Description=Graph Application Service
    After=network.target

    [Service]
    User=ec2-user
    WorkingDirectory=/home/ec2-user/app
    Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
    ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5001 --workers 4 --timeout 120 api:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOL

    # Enable and start service
    systemctl daemon-reload
    systemctl enable graphapp
    systemctl start graphapp

    # Set up logging
    touch /home/ec2-user/app/app.log
    chown ec2-user:ec2-user /home/ec2-user/app/app.log
    chmod 644 /home/ec2-user/app/app.log
  EOF

  tags = {
    Name = "GraphWordInstance"
  }
}

# Outputs
output "api_endpoint" {
  value = "http://${aws_instance.graph_ec2.public_ip}"
}

output "connection_command" {
  value = "aws ssm start-session --target ${aws_instance.graph_ec2.id}"
}