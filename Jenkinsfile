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
  - name: dependency-check
    image: owasp/dependency-check:latest
    command: 
      - sleep
    args:
      - "infinity"
    tty: true        
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
      items:
      - key: .dockerconfigjson
        path: config.json
"""
    }
  }

  environment {
    REGISTRY = "docker.io/stephsc30"
    IMAGE_NAME = "juice-shop"
    IMAGE_TAG = "${BUILD_NUMBER}"
  }

  stages {

    stage('SAST - SonarQube') {
    steps {
        script {
            def scannerHome = tool 'sonarscanner'
            withSonarQubeEnv('sonarqube') {
                sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=juice-shop -Dsonar.sources=."
            }
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
        withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_KEY')]) {
          container('dependency-check') {
            sh '''
              /usr/share/dependency-check/bin/dependency-check.sh \
                --scan . \
                --format XML \
                --out . \
                --nvdApiKey $NVD_KEY
            '''
          }
        }
        dependencyCheckPublisher pattern: 'dependency-check-report.xml'
      }
    }




    stage('Build Image - Kaniko') {
      steps {
        container('kaniko') {
          sh 'pwd'
          sh 'ls -la /kaniko/.docker'
          sh 'cat /kaniko/.docker/config.json'

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
          sh '''
          # Scan and generate JSON report
          trivy image --severity HIGH,CRITICAL \
            --format json \
            -o trivy-report.json \
            $REGISTRY/$IMAGE_NAME:$IMAGE_TAG
          
          # Generate HTML report
          trivy image \
            --severity HIGH,CRITICAL \
            --format template \
            --template "@contrib/html.tpl" \
            -o trivy-report.html \
            $REGISTRY/$IMAGE_NAME:$IMAGE_TAG  

          # Extract vulnerability counts
          CRITICAL=$(cat trivy-report.json | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
          HIGH=$(cat trivy-report.json | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length')  

          echo "-----------------------------------"
          echo "Vulnerability Summary"
          echo "High: $HIGH"
          echo "Critical: $CRITICAL"
          echo "-----------------------------------"

                  # Fail only if Critical > 150
          if [ "$CRITICAL" -gt 150 ]; then
            echo "Critical vulnerabilities exceed threshold (150). Failing build."
            exit 1
          fi
          '''
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
