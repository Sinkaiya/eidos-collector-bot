#!/usr/bin/env groovy

pipeline
    {
        agent any
            options
                {
                    timeout(time: 45, unit: 'SECONDS')
                }
        stages
            {
                stage('Build')
                    {
                        steps
                            {
                                echo 'Building...'
                                sh 'cp /home/sinkaiya/eidos-collector-bot/config.ini ./'
                                sh 'docker build --tag=eidosbot .'
                            }
                    }
                stage('Run')
                    {
                        steps
                            {
                                echo 'Deploying...'
                                sh 'docker stop eidosbot'
                                sh 'docker rm eidosbot'
                                sh 'docker run --detach --name eidosbot --restart=always --network="host" eidosbot'
                            }
                    }
            }
    }