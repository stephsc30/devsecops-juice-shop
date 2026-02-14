pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: 
      - sleep
    args:
      - "infinity"
    tty: true
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  - name: trivy
    image: aquasec/trivy:latest
    command: 
      - sleep
    args:
      - "9999999"  
    tty: true
  - name: zap
    image: ghcr.io/zaproxy/zaproxy:stable
    command: 
      - sleep
    args:
      - "9999999"  
    tty: true
  volumes:
  - name: docker-config
    secret:
      secretName: dockerhub-secret
"""
    }
  }

  environment {
    REGISTRY = "docker.io/stephsc30"
    IMAGE_NAME = "juice-shop"
    IMAGE_TAG = "${BUILD_NUMBER}"
  }

  stages {

    stage('Checkout') {
      steps {
        git 'https://github.com/stephsc30/devsecops-juice-shop.git'
      }
    }

    stage('SAST - SonarQube') {
      steps {
        withSonarQubeEnv('sonarqube') {
          sh """
          sonar-scanner \
          -Dsonar.projectKey=juice-shop \
          -Dsonar.sources=.
          """
        }
      }
    }

    stage('Quality Gate') {
      steps {
        timeout(time: 2, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Dependency Scan') {
      steps {
        dependencyCheck additionalArguments: '--scan .', odcInstallation: 'OWASP'
        dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
      }
    }

    stage('Build Image - Kaniko') {
      steps {
        container('kaniko') {
          sh """
          /kaniko/executor \
            --context=`pwd` \
            --dockerfile=Dockerfile \
            --destination=$REGISTRY/$IMAGE_NAME:$IMAGE_TAG
          """
        }
      }
    }

    stage('Container Scan - Trivy') {
      steps {
        container('trivy') {
          sh """
          trivy image --severity HIGH,CRITICAL \
          --exit-code 1 \
          $REGISTRY/$IMAGE_NAME:$IMAGE_TAG
          """
        }
      }
    }

    stage('Deploy') {
      steps {
        sh """
        sed -i "s|IMAGE_TAG|$REGISTRY/$IMAGE_NAME:$IMAGE_TAG|" deployment.yaml
        kubectl apply -f deployment.yaml
        kubectl apply -f service.yaml
        """
      }
    }

    stage('DAST - OWASP ZAP') {
      steps {
        container('zap') {
          sh """
          zap-baseline.py \
          -t http://juice-shop:5000 \
          -r zap-report.html
          """
        }
      }
    }
  }

  post {
    always {
      publishHTML(target: [
        allowMissing: false,
        alwaysLinkToLastBuild: true,
        keepAll: true,
        reportDir: '.',
        reportFiles: 'zap-report.html',
        reportName: 'ZAP Report'
      ])
    }
  }
}
