export interface NavLinkItem {
  href: string;
  label: string;
  current?: boolean;
}

export interface NavLinksProps {
  links: NavLinkItem[];
}

export function NavLinks({ links }: NavLinksProps) {
  return (
    <nav className="ds-top-nav">
      {links.map((link, i) => (
        <a key={i} href={link.href} aria-current={link.current ? 'page' : undefined}>
          {link.label}
        </a>
      ))}
    </nav>
  );
}
