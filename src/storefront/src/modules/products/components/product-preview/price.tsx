import { Text, clx } from "@medusajs/ui"
import { VariantPrice } from "types/global"

export default async function PreviewPrice({ price }: { price: VariantPrice }) {
  if (!price) {
    return null
  }

  return (
    <>
      {price.price_type === "sale" && (
        <Text
          className="line-through text-ui-fg-muted"
          data-testid="original-price"
        >
          {price.original_price}
        </Text>
      )}
      <Text
        className={clx(
          "font-display font-semibold text-brand-ink tracking-wide",
          {
            "text-ui-fg-interactive": price.price_type === "sale",
          }
        )}
        data-testid="price"
      >
        {price.calculated_price}
      </Text>
    </>
  )
}
