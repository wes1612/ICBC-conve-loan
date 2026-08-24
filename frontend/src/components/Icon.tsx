import type { SVGProps } from 'react'

export type IconName =
  | 'arrow'
  | 'bank'
  | 'building'
  | 'camera'
  | 'check'
  | 'chevron'
  | 'database'
  | 'document'
  | 'download'
  | 'fingerprint'
  | 'lock'
  | 'refresh'
  | 'shield'
  | 'smiley'
  | 'spark'
  | 'upload'
  | 'warning'

const paths: Record<IconName, JSX.Element> = {
  arrow: <><path d="M5 12h14"/><path d="m14 7 5 5-5 5"/></>,
  bank: <><path d="m3 10 9-6 9 6"/><path d="M5 10h14"/><path d="M7 10v7M12 10v7M17 10v7"/><path d="M4 20h16"/></>,
  building: <><path d="M4 21V5a2 2 0 0 1 2-2h8v18"/><path d="M14 9h4a2 2 0 0 1 2 2v10"/><path d="M8 7h2M8 11h2M8 15h2M17 13h.01M17 17h.01"/></>,
  camera: <><path d="M14.5 4 16 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3l1.5-3z"/><circle cx="12" cy="13" r="3"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  chevron: <path d="m9 18 6-6-6-6"/>,
  database: <><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></>,
  document: <><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5M9 13h6M9 17h6M9 9h2"/></>,
  download: <><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></>,
  fingerprint: <><path d="M12 11a2 2 0 0 1 2 2c0 3-.8 5.6-2.1 7.7"/><path d="M8.2 20.7A14 14 0 0 0 10 13a2 2 0 1 1 4 0"/><path d="M6.5 17.9A12 12 0 0 0 8 13a4 4 0 0 1 8 0c0 2.6-.4 5-1.2 7"/><path d="M4.8 15.5A10 10 0 0 0 5 13a7 7 0 0 1 14 0c0 1.1-.1 2.2-.2 3.2"/></>,
  lock: <><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></>,
  refresh: <><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.6-2.6L20 8M4 16l2.3 2.6A7 7 0 0 0 18 16"/></>,
  shield: <><path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10"/><path d="m9 12 2 2 4-5"/></>,
  smiley: <><path d="M8.2 7.2v3"/><path d="M15.8 7.2v3"/><path d="M7.2 13.2c.8 2.3 2.5 3.6 4.8 3.6s4-1.3 4.8-3.6"/></>,
  spark: <><path d="m12 3-1.2 3.8L7 8l3.8 1.2L12 13l1.2-3.8L17 8l-3.8-1.2z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7zM19 14l-.6 1.9-1.9.6 1.9.6.6 1.9.6-1.9 1.9-.6-1.9-.6z"/></>,
  upload: <><path d="M12 21V8"/><path d="m7 13 5-5 5 5"/><path d="M5 3h14"/></>,
  warning: <><path d="M10.3 3.6 2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0"/><path d="M12 9v4M12 17h.01"/></>,
}

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
  size?: number
}

export function Icon({ name, size = 20, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {paths[name]}
    </svg>
  )
}
