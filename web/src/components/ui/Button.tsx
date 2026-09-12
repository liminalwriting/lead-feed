import type {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

export type ButtonVariant = "primary" | "secondary";
export type ButtonSize = "m";

type CommonProps = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
  className?: string;
};

type ButtonAsButton = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children"> & {
    href?: undefined;
  };

type ButtonAsLink = CommonProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "className" | "children"> & {
    href: string;
  };

export type ButtonProps = ButtonAsButton | ButtonAsLink;

const variantClass: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-surface hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50",
  secondary:
    "border border-border bg-surface text-ink hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-50",
};

const sizeClass: Record<ButtonSize, string> = {
  m: "rounded-lf px-4 py-2 text-sm font-medium",
};

function cx(...parts: Array<string | false | undefined>) {
  return parts.filter(Boolean).join(" ");
}

function buttonClassName(
  variant: ButtonVariant,
  size: ButtonSize,
  className?: string,
) {
  return cx(
    "inline-flex items-center justify-center transition-colors",
    variantClass[variant],
    sizeClass[size],
    className,
  );
}

/**
 * Design-system Button.
 * Variants: Primary, Secondary. Sizes: M.
 * Pass `href` to render as a link with the same styles.
 */
export function Button({
  variant = "primary",
  size = "m",
  className,
  children,
  ...rest
}: ButtonProps) {
  const classes = buttonClassName(variant, size, className);

  if ("href" in rest && rest.href) {
    const { href, ...anchorRest } = rest;
    return (
      <a href={href} className={classes} {...anchorRest}>
        {children}
      </a>
    );
  }

  const { type = "button", ...buttonRest } = rest as ButtonAsButton;
  return (
    <button type={type} className={classes} {...buttonRest}>
      {children}
    </button>
  );
}
