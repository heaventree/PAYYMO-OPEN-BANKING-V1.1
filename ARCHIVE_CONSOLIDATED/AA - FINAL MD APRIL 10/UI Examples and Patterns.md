# __UI Examples and Patterns__

This document provides concrete code examples for core UI components and page structures, based on the patterns derived from the Heaventree Admin Template and aligned with our project's tech stack \(React, TypeScript, Tailwind CSS\)\.

*\(These examples should be documented and tested within Storybook as per UI\_Design\_System\_Architecture\.md\)*

## __Base Components \(02\-ui\-components\.md content\)__

### __Button Component__

// Example Location: src/components/ui/Button\.tsx  
import React from 'react';  
import \{ clsx \} from 'clsx'; // Utility for conditionally joining class names  
import \{ twMerge \} from 'tailwind\-merge'; // Utility to merge Tailwind classes intelligently  
  
interface ButtonProps extends React\.ButtonHTMLAttributes<HTMLButtonElement> \{  
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'; // Added danger variant  
  size?: 'sm' | 'md' | 'lg';  
  isLoading?: boolean;  
  children: React\.ReactNode;  
\}  
  
export function Button\(\{  
  variant = 'primary',  
  size = 'md',  
  isLoading = false,  
  className,  
  children,  
  disabled,  
  \.\.\.props  
\}: ButtonProps\) \{  
  const baseStyles = 'inline\-flex items\-center justify\-center rounded\-md font\-medium transition\-colors focus\-visible:outline\-none focus\-visible:ring\-2 focus\-visible:ring\-ring focus\-visible:ring\-offset\-2 disabled:pointer\-events\-none disabled:opacity\-50';  
  
  // Define variant styles using project's Tailwind theme colors \(adjust as needed\)  
  const variants = \{  
    primary: 'bg\-primary text\-primary\-foreground hover:bg\-primary/90',  
    secondary: 'bg\-secondary text\-secondary\-foreground hover:bg\-secondary/80',  
    outline: 'border border\-input bg\-background hover:bg\-accent hover:text\-accent\-foreground',  
    ghost: 'hover:bg\-accent hover:text\-accent\-foreground',  
    danger: 'bg\-destructive text\-destructive\-foreground hover:bg\-destructive/90', // Example danger  
  \};  
  
  const sizes = \{  
    sm: 'h\-8 px\-3 text\-sm',  
    md: 'h\-10 px\-4 text\-sm',  
    lg: 'h\-12 px\-6 text\-base'  
  \};  
  
  return \(  
    <button  
      className=\{twMerge\( // Use twMerge to handle conflicting classes gracefully  
        clsx\( // Use clsx for conditional classes  
          baseStyles,  
          variants\[variant\],  
          sizes\[size\],  
          isLoading && 'cursor\-wait', // Apply loading style if needed  
          className // Allow custom classes to be passed  
        \)  
      \)\}  
      disabled=\{disabled || isLoading\}  
      \{\.\.\.props\}  
    >  
      \{isLoading ? \(  
        <>  
          \{/\* Simple SVG Spinner \*/\}  
          <svg  
            className="\-ml\-1 mr\-2 h\-4 w\-4 animate\-spin" // Adjusted margin  
            xmlns="http://www\.w3\.org/2000/svg"  
            fill="none"  
            viewBox="0 0 24 24"  
          >  
            <circle  
              className="opacity\-25"  
              cx="12"  
              cy="12"  
              r="10"  
              stroke="currentColor"  
              strokeWidth="4"  
            />  
            <path  
              className="opacity\-75"  
              fill="currentColor"  
              d="M4 12a8 8 0 018\-8V0C5\.373 0 0 5\.373 0 12h4zm2 5\.291A7\.962 7\.962 0 014 12H0c0 3\.042 1\.135 5\.824 3 7\.938l3\-2\.647z"  
            />  
          </svg>  
          Loading\.\.\.  
        </>  
      \) : \(  
        children  
      \)\}  
    </button>  
  \);  
\}  


### __Card Component__

// Example Location: src/components/ui/Card\.tsx  
import React from 'react';  
import \{ twMerge \} from 'tailwind\-merge';  
import \{ clsx \} from 'clsx';  
  
interface CardProps extends React\.HTMLAttributes<HTMLDivElement> \{\}  
interface CardHeaderProps extends React\.HTMLAttributes<HTMLDivElement> \{\}  
interface CardTitleProps extends React\.HTMLAttributes<HTMLHeadingElement> \{\}  
interface CardDescriptionProps extends React\.HTMLAttributes<HTMLParagraphElement> \{\}  
interface CardContentProps extends React\.HTMLAttributes<HTMLDivElement> \{\}  
interface CardFooterProps extends React\.HTMLAttributes<HTMLDivElement> \{\}  
  
export function Card\(\{ className, children, \.\.\.props \}: CardProps\) \{  
  return \(  
    <div  
      className=\{twMerge\(  
        "rounded\-xl border bg\-card text\-card\-foreground shadow", // Adjusted for common theme variable names  
        className  
      \)\}  
      \{\.\.\.props\}  
    >  
      \{children\}  
    </div>  
  \);  
\}  
  
export function CardHeader\(\{ className, children, \.\.\.props \}: CardHeaderProps\) \{  
  return \(  
    <div className=\{twMerge\("flex flex\-col space\-y\-1\.5 p\-6", className\)\} \{\.\.\.props\}> \{/\* Added padding \*/\}  
      \{children\}  
    </div>  
  \);  
\}  
  
export function CardTitle\(\{ className, children, \.\.\.props \}: CardTitleProps\) \{  
  return \(  
    <h3 className=\{twMerge\("font\-semibold leading\-none tracking\-tight", className\)\} \{\.\.\.props\}> \{/\* Use h3 for semantics \*/\}  
      \{children\}  
    </h3>  
  \);  
\}  
  
export function CardDescription\(\{ className, children, \.\.\.props \}: CardDescriptionProps\) \{  
  return \(  
    <p className=\{twMerge\("text\-sm text\-muted\-foreground", className\)\} \{\.\.\.props\}>  
      \{children\}  
    </p>  
  \);  
\}  
  
export function CardContent\(\{ className, children, \.\.\.props \}: CardContentProps\) \{  
  return \(  
    <div className=\{twMerge\("p\-6 pt\-0", className\)\} \{\.\.\.props\}> \{/\* Added padding \*/\}  
      \{children\}  
    </div>  
  \);  
\}  
  
export function CardFooter\(\{ className, children, \.\.\.props \}: CardFooterProps\) \{  
  return \(  
    <div className=\{twMerge\("flex items\-center p\-6 pt\-0", className\)\} \{\.\.\.props\}> \{/\* Added padding \*/\}  
      \{children\}  
    </div>  
  \);  
\}  


### __Loading Spinner Component__

// Example Location: src/components/ui/LoadingSpinner\.tsx  
import React from 'react';  
import \{ twMerge \} from 'tailwind\-merge';  
import \{ clsx \} from 'clsx';  
  
interface LoadingSpinnerProps extends React\.SVGProps<SVGSVGElement> \{  
    size?: 'sm' | 'md' | 'lg';  
\}  
  
export function LoadingSpinner\(\{ className, size = 'md', \.\.\.props \}: LoadingSpinnerProps\) \{  
    const sizes = \{  
        sm: 'h\-4 w\-4',  
        md: 'h\-8 w\-8',  
        lg: 'h\-12 w\-12',  
    \};  
    return \(  
        <svg  
            xmlns="http://www\.w3\.org/2000/svg"  
            width="24"  
            height="24"  
            viewBox="0 0 24 24"  
            fill="none"  
            stroke="currentColor"  
            strokeWidth="2"  
            strokeLinecap="round"  
            strokeLinejoin="round"  
            className=\{twMerge\("animate\-spin", sizes\[size\], className\)\}  
            role="status" // Added role  
            aria\-label="Loading" // Added aria\-label  
            \{\.\.\.props\}  
        >  
            <path d="M21 12a9 9 0 1 1\-6\.219\-8\.56" />  
            <span className="sr\-only">Loading\.\.\.</span> \{/\* Added screen reader text \*/\}  
        </svg>  
    \);  
\}  


### __Error Boundary Component__

// Example Location: src/components/ErrorBoundary\.tsx  
import React, \{ Component, ErrorInfo, ReactNode \} from 'react';  
import \{ Button \} from '\./ui/Button'; // Assuming Button component exists  
  
interface Props \{  
  children: ReactNode;  
  fallbackMessage?: string; // Optional custom message  
\}  
  
interface State \{  
  hasError: boolean;  
  error: Error | null;  
\}  
  
export class ErrorBoundary extends Component<Props, State> \{  
  public state: State = \{  
    hasError: false,  
    error: null  
  \};  
  
  public static getDerivedStateFromError\(error: Error\): State \{  
    // Update state so the next render will show the fallback UI\.  
    return \{ hasError: true, error \};  
  \}  
  
  public componentDidCatch\(error: Error, errorInfo: ErrorInfo\) \{  
    // You can also log the error to an error reporting service  
    // logErrorToMyService\(error, errorInfo\);  
    console\.error\('ErrorBoundary caught an error:', error, errorInfo\);  
  \}  
  
  public render\(\) \{  
    if \(this\.state\.hasError\) \{  
      // You can render any custom fallback UI  
      return \(  
        <div role="alert" className="flex min\-h\-\[50vh\] items\-center justify\-center p\-4">  
          <div className="max\-w\-md w\-full p\-6 bg\-card text\-card\-foreground rounded\-lg shadow\-lg border border\-destructive">  
            <h2 className="text\-xl font\-semibold text\-destructive mb\-4">  
              Something went wrong  
            </h2>  
            <p className="text\-muted\-foreground mb\-4">  
              \{this\.props\.fallbackMessage || "We apologize for the inconvenience\. Please try refreshing the page or contact support if the problem persists\."\}  
            </p>  
            \{/\* Optional: Display error details in development \*/\}  
            \{process\.env\.NODE\_ENV === 'development' && this\.state\.error && \(  
                <details className="mb\-4 text\-xs text\-muted\-foreground/80">  
                    <summary>Error Details</summary>  
                    <pre className="mt\-2 whitespace\-pre\-wrap break\-words">\{this\.state\.error\.toString\(\)\}</pre>  
                </details>  
            \)\}  
            <div className="flex justify\-center">  
              <Button  
                onClick=\{\(\) => window\.location\.reload\(\)\}  
                variant="destructive"  
                aria\-label="Refresh page"  
              >  
                Refresh Page  
              </Button>  
            </div>  
          </div>  
        </div>  
      \);  
    \}  
  
    return this\.props\.children;  
  \}  
\}  


## __Page Component Examples \(03\-page\-components\.md content\)__

*\(Note: Assumes React Router \(react\-router\-dom\) is used for routing and <Link to="\.\.\."> is the appropriate component\)*

### __Landing Page Example__

// Example Location: src/pages/LandingPage\.tsx  
import React from 'react';  
// IMPORTANT: Use Link from your chosen router \(e\.g\., react\-router\-dom\)  
import \{ Link \} from 'react\-router\-dom'; // Adapted from Wouter  
import \{ CheckCircle, ArrowRight \} from 'lucide\-react';  
import \{ Button \} from '@/components/ui/Button'; // Use project's Button  
import \{ Card, CardContent, CardDescription, CardHeader, CardTitle \} from '@/components/ui/Card'; // Use project's Card  
  
export function LandingPage\(\) \{  
  const features = \[  
    'WCAG 2\.1 Compliance Testing',  
    'Automated Accessibility Scans',  
    'Color Contrast Analysis',  
    'Detailed Reporting',  
    'Real\-time Monitoring'  
  \];  
  
  return \(  
    <div className="py\-12">  
      <div className="max\-w\-7xl mx\-auto px\-4 sm:px\-6 lg:px\-8">  
        \{/\* Hero Section \*/\}  
        <div className="text\-center">  
          <h1 className="text\-4xl font\-bold text\-foreground dark:text\-foreground sm:text\-5xl md:text\-6xl">  
            Web Accessibility Testing Platform  
          </h1>  
          <p className="mt\-3 max\-w\-md mx\-auto text\-base text\-muted\-foreground dark:text\-muted\-foreground sm:text\-lg md:mt\-5 md:text\-xl md:max\-w\-3xl">  
            Comprehensive WCAG compliance checks and actionable insights for developers and designers\.  
          </p>  
          \{/\* CTA Buttons \*/\}  
          <div className="mt\-8 flex justify\-center gap\-4">  
            <Link to="/checker"> \{/\* Adapted from Wouter \*/\}  
              <Button size="lg" className="gap\-2">  
                Start Testing <ArrowRight className="w\-5 h\-5" />  
              </Button>  
            </Link>  
            <Link to="/tools/wcag\-standards"> \{/\* Adapted from Wouter \*/\}  
              <Button variant="outline" size="lg">  
                Learn More  
              </Button>  
            </Link>  
          </div>  
        </div>  
  
        \{/\* Features Grid \*/\}  
        <div className="mt\-16 grid gap\-8 md:grid\-cols\-2 lg:grid\-cols\-3">  
          \{features\.map\(\(feature, index\) => \(  
            <Card key=\{index\}>  
              <CardHeader>  
                <CardTitle className="flex items\-center gap\-2">  
                  <CheckCircle className="w\-5 h\-5 text\-primary" /> \{/\* Use primary color token \*/\}  
                  \{feature\}  
                </CardTitle>  
              </CardHeader>  
              <CardContent>  
                <CardDescription>  
                  Ensure your web applications meet the highest accessibility standards with our comprehensive testing tools\.  
                </CardDescription>  
              </CardContent>  
            </Card>  
          \)\)\}  
        </div>  
      </div>  
    </div>  
  \);  
\}  


### __WCAG Checker Page Example__

// Example Location: src/pages/CheckerPage\.tsx  
import React, \{ useState \} from 'react';  
import \{ Button \} from '@/components/ui/Button'; // Use project's Button  
import \{ Card, CardContent, CardDescription, CardHeader, CardTitle \} from '@/components/ui/Card'; // Use project's Card  
import \{ ArrowRight \} from 'lucide\-react';  
// Assuming an Input component exists or use standard input  
// import \{ Input \} from '@/components/ui/Input';  
  
export function WCAGCheckerPage\(\) \{  
  const \[url, setUrl\] = useState\(''\);  
  const \[isScanning, setIsScanning\] = useState\(false\);  
  const \[scanResults, setScanResults\] = useState<any>\(null\); // Replace 'any' with actual result type  
  const \[error, setError\] = useState<string | null>\(null\);  
  
  const handleScan = async \(\) => \{  
    setIsScanning\(true\);  
    setError\(null\);  
    setScanResults\(null\);  
    try \{  
      // Replace with actual scanning logic calling backend API  
      console\.log\('Scanning URL:', url\);  
      await new Promise\(resolve => setTimeout\(resolve, 1500\)\); // Simulate API call  
      // setScanResults\(resultsFromApi\);  
      setScanResults\(\{ message: \`Scan complete for $\{url\}\. Results placeholder\.\` \}\); // Placeholder  
    \} catch \(err\) \{  
        setError\('Failed to scan the URL\. Please try again\.'\);  
        console\.error\(err\);  
    \} finally \{  
        setIsScanning\(false\);  
    \}  
  \};  
  
  return \(  
    <div className="max\-w\-4xl mx\-auto">  
      <h1 className="text\-3xl font\-bold mb\-8">  
        WCAG Accessibility Checker  
      </h1>  
      <Card className="mb\-6">  
        <CardHeader>  
          <CardTitle>Enter Website URL</CardTitle>  
          <CardDescription>  
            Enter the website URL you want to scan for accessibility issues\.  
          </CardDescription>  
        </CardHeader>  
        <CardContent>  
          <div className="flex flex\-col sm:flex\-row gap\-4">  
            <input // Replace with project's Input component if available  
              id="url\-input"  
              type="url"  
              value=\{url\}  
              onChange=\{\(e\) => setUrl\(e\.target\.value\)\}  
              placeholder="https://example\.com"  
              className="flex\-1 h\-10 w\-full rounded\-md border border\-input bg\-transparent px\-3 py\-2 text\-sm ring\-offset\-background file:border\-0 file:bg\-transparent file:text\-sm file:font\-medium placeholder:text\-muted\-foreground focus\-visible:outline\-none focus\-visible:ring\-2 focus\-visible:ring\-ring focus\-visible:ring\-offset\-2 disabled:cursor\-not\-allowed disabled:opacity\-50" // Basic input style  
              aria\-label="Website URL"  
              aria\-describedby="scan\-error" // Link error message  
            />  
            <Button  
              onClick=\{handleScan\}  
              isLoading=\{isScanning\}  
              disabled=\{isScanning || \!url\}  
              className="whitespace\-nowrap"  
            >  
              Start Scan <ArrowRight className="ml\-2 h\-4 w\-4" />  
            </Button>  
          </div>  
           \{error && <p id="scan\-error" className="mt\-2 text\-sm text\-destructive">\{error\}</p>\}  
        </CardContent>  
      </Card>  
  
      \{/\* Results Section \*/\}  
      \{isScanning && \(  
        <div className="text\-center p\-4">  
            <p>Scanning in progress\.\.\.</p>  
            \{/\* Consider adding LoadingSpinner here \*/\}  
        </div>  
      \)\}  
      \{scanResults && \!isScanning && \(  
        <Card>  
            <CardHeader><CardTitle>Scan Results</CardTitle></CardHeader>  
            <CardContent>  
                \{/\* Render actual scan results here \*/\}  
                <pre>\{JSON\.stringify\(scanResults, null, 2\)\}</pre>  
            </CardContent>  
        </Card>  
      \)\}  
  
    </div>  
  \);  
\}  


### __WCAG Standards Table Page Example__

// Example Location: src/pages/StandardsPage\.tsx  
import React from 'react';  
import \{ Card, CardContent, CardDescription, CardHeader, CardTitle \} from '@/components/ui/Card'; // Use project's Card  
  
// Data ideally fetched from a CMS or constants file  
const wcagPrinciples = \[  
  \{  
    principle: 'Perceivable',  
    guidelines: \[ 'Text Alternatives', 'Time\-based Media', 'Adaptable', 'Distinguishable'\]  
  \},  
  \{  
    principle: 'Operable',  
    guidelines: \[ 'Keyboard Accessible', 'Enough Time', 'Seizures and Physical Reactions', 'Navigable', 'Input Modalities \(WCAG 2\.1\)'\]  
  \},  
  \{  
    principle: 'Understandable',  
    guidelines: \[ 'Readable', 'Predictable', 'Input Assistance' \]  
  \},  
  \{  
    principle: 'Robust',  
    guidelines: \[ 'Compatible' \]  
  \}  
\];  
  
export function WCAGStandardsTablePage\(\) \{  
  return \(  
    <div className="max\-w\-6xl mx\-auto">  
      <h1 className="text\-3xl font\-bold mb\-4"> \{/\* Reduced margin \*/\}  
        WCAG 2\.1 Guidelines Reference  
      </h1>  
      <p className="text\-muted\-foreground mb\-8"> \{/\* Use theme color \*/\}  
        A summary of the Web Content Accessibility Guidelines \(WCAG\) 2\.1 principles\. Refer to the official documentation for full success criteria\.  
      </p>  
  
      <div className="grid gap\-6 md:grid\-cols\-2"> \{/\* Adjusted gap \*/\}  
        \{wcagPrinciples\.map\(\(section\) => \(  
          <Card key=\{section\.principle\}>  
            <CardHeader>  
              <CardTitle>\{section\.principle\}</CardTitle>  
              <CardDescription>  
                Key guidelines for making content \{section\.principle\.toLowerCase\(\)\}\.  
              </CardDescription>  
            </CardHeader>  
            <CardContent>  
              <ul className="space\-y\-2 list\-disc list\-inside"> \{/\* Use list style \*/\}  
                \{section\.guidelines\.map\(\(guideline\) => \(  
                  <li key=\{guideline\} className="text\-sm"> \{/\* Ensure text size consistency \*/\}  
                    \{guideline\}  
                  </li>  
                \)\)\}  
              </ul>  
            </CardContent>  
          </Card>  
        \)\)\}  
      </div>  
    </div>  
  \);  
\}  


