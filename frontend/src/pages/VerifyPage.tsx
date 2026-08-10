import { useState } from 'react'
import { Icon } from '../components/Icon'
import { Button, Eyebrow, InfoNote } from '../components/Ui'

interface VerifyPageProps {
  legalName: string
  onBack: () => void
  onNext: () => void
}

export function VerifyPage({ legalName, onBack, onNext }: VerifyPageProps) {
  const [verified, setVerified] = useState(false)
  const [scanning, setScanning] = useState(false)

  const startScan = () => {
    setScanning(true)
    window.setTimeout(() => {
      setScanning(false)
      setVerified(true)
    }, 900)
  }

  return (
    <main className="verify-page page-shell">
      <div className="verify-copy">
        <Eyebrow>步骤 02 · 法人核验</Eyebrow>
        <h1>确认本人操作，<br />保护企业信用。</h1>
        <p>正式版本将接入实名与活体检测服务。当前交互仅用于演示申请流程，不采集或上传影像。</p>
        <div className="verify-points">
          <div><Icon name="shield" /><span><strong>最小化采集</strong>只处理完成核验所需信息</span></div>
          <div><Icon name="fingerprint" /><span><strong>本人授权</strong>核验前明确告知使用目的</span></div>
          <div><Icon name="lock" /><span><strong>传输保护</strong>生产环境需接入合规认证服务</span></div>
        </div>
        <InfoNote tone="warning">人脸识别和短信验证尚未在当前后端实现，本页不会伪造真实认证结果。</InfoNote>
      </div>

      <section className={`verify-device ${verified ? 'is-verified' : ''}`}>
        <div className="verify-device__top"><span /><strong>法人活体核验</strong><small>演示</small></div>
        <div className="face-stage">
          <div className={`face-frame ${scanning ? 'is-scanning' : ''}`}>
            <Icon name={verified ? 'check' : 'camera'} size={52} />
            <i className="corner corner--tl" /><i className="corner corner--tr" /><i className="corner corner--bl" /><i className="corner corner--br" />
            {scanning && <span className="scan-line" />}
          </div>
          <h2>{verified ? '演示核验已完成' : scanning ? '正在进行演示核验…' : `请 ${legalName || '法人'} 正对屏幕`}</h2>
          <p>{verified ? '可继续填写经营资料' : '保持光线充足，请勿佩戴口罩或墨镜'}</p>
        </div>
        {!verified ? <Button onClick={startScan} disabled={scanning}>{scanning ? '识别中…' : '开始演示核验'}</Button> : <Button icon="arrow" onClick={onNext}>继续填写资料</Button>}
      </section>

      <div className="workflow__actions workflow__actions--verify">
        <Button variant="ghost" onClick={onBack}>返回修改资料</Button>
      </div>
    </main>
  )
}
