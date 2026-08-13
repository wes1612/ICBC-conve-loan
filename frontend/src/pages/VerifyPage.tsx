import { useState } from 'react'
import { Icon } from '../components/Icon'
import { Button, Eyebrow } from '../components/Ui'

interface VerifyPageProps {
  legalName: string
  verified: boolean
  onVerifiedChange: (verified: boolean) => void
  onBack: () => void
  onNext: () => void
}

export function VerifyPage({ legalName, verified, onVerifiedChange, onBack, onNext }: VerifyPageProps) {
  const [showQr, setShowQr] = useState(false)

  const startScan = () => {
    setShowQr(true)
    window.setTimeout(() => {
      onVerifiedChange(true)
    }, 1100)
  }

  return (
    <main className="verify-page verify-page--center page-shell">
      <Eyebrow>02 · 身份核验</Eyebrow>
      <section className={`verify-device ${verified ? 'is-verified' : ''}`}>
        <h1>法人人脸核验</h1>
        <div className="face-stage">
          <div className="portrait-frame">
            {verified ? <Icon name="check" size={58} /> : <><span className="portrait-head" /><span className="portrait-body" /></>}
          </div>
          <h2>{verified ? '演示核验已完成' : `${legalName || '法人'} 待核验`}</h2>
        </div>
        {!verified ? <Button onClick={startScan}>开始演示核验</Button> : <Button icon="arrow" onClick={onNext}>下一页</Button>}
      </section>

      {showQr && (
        <div className="qr-modal" role="dialog" aria-modal="true" aria-label="演示二维码">
          <div className="qr-card">
            <button type="button" className="qr-close" onClick={() => setShowQr(false)}>×</button>
            <h2>请使用法人手机扫码</h2>
            <div className="qr-code" aria-hidden="true">{Array.from({ length: 49 }).map((_, index) => <span key={index} className={index % 3 === 0 || index % 7 === 0 ? 'is-dark' : ''} />)}</div>
            <p>手机端将打开微信扫脸程序完成法人人脸核验演示。</p>
          </div>
        </div>
      )}

      <div className="workflow__actions workflow__actions--verify">
        <Button variant="ghost" onClick={onBack}>上一页</Button>
      </div>
    </main>
  )
}
