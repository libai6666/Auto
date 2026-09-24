pipeline {
    agent any
    
    options {
        timeout(time: 1, unit: 'HOURS')
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        PYTHON_PATH = 'python'
    }
    
    parameters {
        choice(
            name: 'ENV',
            choices: ['test', 'dev', 'prod'],
            description: '选择测试环境'
        )
        choice(
            name: 'MARKER',
            choices: ['', 'smoke', 'regression', 'api', 'high', 'medium'],
            description: '选择测试标记（留空表示执行全部）'
        )
        string(
            name: 'PARALLEL',
            defaultValue: '0',
            description: '并行执行进程数（0表示不并行）'
        )
        string(
            name: 'RERUNS',
            defaultValue: '2',
            description: '失败重试次数'
        )
        booleanParam(
            name: 'SEND_DINGTALK',
            defaultValue: true,
            description: '是否发送钉钉通知'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '========== 阶段1: 拉取代码 =========='
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                echo '========== 阶段2: 环境准备 =========='
                bat '''
                    python --version
                    pip --version
                    pip install -r requirements.txt -q
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo '========== 阶段3: 执行测试 =========='
                script {
                    def cmd = "python run.py --env ${params.ENV} --allure"
                    
                    if (params.MARKER) {
                        cmd += " --marker ${params.MARKER}"
                    }
                    if (params.PARALLEL != '0') {
                        cmd += " --xdist ${params.PARALLEL}"
                    }
                    if (params.RERUNS != '0') {
                        cmd += " --reruns ${params.RERUNS}"
                    }
                    if (params.SEND_DINGTALK) {
                        cmd += " --dingtalk"
                    }
                    
                    echo "执行命令: ${cmd}"
                    
                    def exitCode = bat(script: cmd, returnStatus: true)
                    
                    if (exitCode != 0) {
                        echo "测试执行完成，存在失败用例（退出码: ${exitCode}）"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Report') {
            steps {
                echo '========== 阶段4: 生成 Allure 报告 =========='
                script {
                    def findCmd = '''
                        @FOR /F "delims=" %%i IN ('dir /b /ad /o-d reports\\allure_results_* 2^>nul') DO @echo reports\\%%i& exit /b
                    '''
                    def resultsDir = bat(script: findCmd, returnStdout: true).trim()
                    
                    if (resultsDir) {
                        echo "使用结果目录: ${resultsDir}"
                        allure([
                            includeProperties: false,
                            jdk: '',
                            reportBuildPolicy: 'ALWAYS',
                            results: [[path: resultsDir]]
                        ])
                    } else {
                        echo "未找到 Allure 结果目录"
                    }
                }
            }
        }
        
        stage('Archive') {
            steps {
                echo '========== 阶段5: 归档日志 =========='
                archiveArtifacts(
                    artifacts: 'logs/*.log',
                    allowEmptyArchive: true,
                    fingerprint: true
                )
            }
        }
    }
    
    post {
        always {
            echo '========== 构建结束 =========='
            echo "构建结果: ${currentBuild.result ?: 'SUCCESS'}"
            echo "构建耗时: ${currentBuild.durationString}"
        }
        success {
            echo '🎉 测试全部通过！'
        }
        unstable {
            echo '⚠️ 测试存在失败用例'
        }
        failure {
            echo '❌ 构建失败'
        }
        cleanup {
            bat '''
                @echo off
                setlocal enabledelayedexpansion
                set count=0
                for /f "delims=" %%i in ('dir /b /ad /o-d reports\\allure_results_* 2^>nul') do (
                    set /a count+=1
                    if !count! gtr 5 (
                        rd /s /q "reports\\%%i" 2>nul
                    )
                )
            '''
        }
    }
}
