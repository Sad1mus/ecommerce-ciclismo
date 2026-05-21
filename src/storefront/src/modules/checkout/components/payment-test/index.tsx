import { Badge } from "@medusajs/ui"

const PaymentTest = ({ className }: { className?: string }) => {
  return (
    <Badge color="orange" className={className}>
      <span className="font-semibold">Atención:</span> Solo para fines de
      prueba.
    </Badge>
  )
}

export default PaymentTest
