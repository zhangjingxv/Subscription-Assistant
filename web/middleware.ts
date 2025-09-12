import { NextResponse, type NextRequest } from 'next/server';
import { i18n, negotiateLocale, isSupportedLocale } from './src/i18n/config';

// Middleware to enforce locale prefix and negotiate from Accept-Language
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip API, static, and Next.js internals
  if (
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/assets') ||
    pathname.startsWith('/favicon') ||
    pathname.startsWith('/robots') ||
    pathname.startsWith('/sitemap')
  ) {
    return NextResponse.next();
  }

  // If path has a supported locale prefix, let it pass
  const segments = pathname.split('/');
  const maybeLocale = segments[1];
  if (isSupportedLocale(maybeLocale)) {
    return NextResponse.next();
  }

  // Decide locale (cookie > header > default)
  const cookieLocale = request.cookies.get('NEXT_LOCALE')?.value;
  const headerLocale = negotiateLocale(request.headers.get('accept-language'));
  const locale = (cookieLocale && isSupportedLocale(cookieLocale)
    ? cookieLocale
    : headerLocale) || i18n.defaultLocale;

  // Rewrite to locale-prefixed path
  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname}`;
  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ['/((?!_next|api|.*\\.\
(?:png|jpg|jpeg|gif|webp|avif|svg|ico|txt)).*)'],
};

