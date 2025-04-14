# __State Management Best Practices \(Updated\)__

## __Core Library: Zustand__

- __Why Zustand?__ Lightweight, minimal boilerplate, leverages hooks, easy async handling\.
- __Store Structure:__ Create separate stores \(slices\) per feature domain \(e\.g\., useAuthStore, useFormStore\)\.

## __State Organization__

- __Keep State Flat:__ Avoid deeply nested objects where possible\.
- __Selectors:__ Use selectors \(memoized with useMemo or Reselect if needed\) to derive data and prevent unnecessary re\-renders\.
- __Computed State:__ Define derived state within the store itself if it's frequently used\.

// Example Zustand Store \(Basic\)  
import \{ create \} from 'zustand';  
  
interface BasicCounterState \{  
  count: number;  
  increment: \(\) => void;  
\}  
  
export const useCounterStore = create<BasicCounterState>\(\(set\) => \(\{  
  count: 0,  
  increment: \(\) => set\(\(state\) => \(\{ count: state\.count \+ 1 \}\)\),  
\}\)\);  


## __State Management Flow Diagram__

graph TD  
    A\[Component Event\] \-\-> B\(Call Store Action\);  
    B \-\-> C\{Update Store State\};  
    C \-\-> D\[State Change Notification\];  
    D \-\-> E\[Component Re\-renders with New State\];  
    F\[Selector\] \-\-> E;  
    C \-\-> F;  


## __Middleware Usage \(New Section\)__

Zustand supports middleware to add extra capabilities like persistence, developer tools integration, or immutable updates\.

- __persist__ Middleware: Save store state to localStorage or sessionStorage\.
- __devtools__ Middleware: Connect the store to Redux DevTools browser extension\.
- __immer__ Middleware: Use Immer for easier immutable updates \(optional, Zustand encourages simple immutable patterns by default\)\.

// Example Store with Middleware  
import \{ create \} from 'zustand';  
import \{ persist, createJSONStorage \} from 'zustand/middleware';  
import \{ devtools \} from 'zustand/middleware';  
// import \{ immer \} from 'zustand/middleware/immer'; // Optional  
  
interface SettingsState \{  
  theme: 'light' | 'dark';  
  notificationsEnabled: boolean;  
  toggleTheme: \(\) => void;  
  setNotifications: \(enabled: boolean\) => void;  
\}  
  
export const useSettingsStore = create<SettingsState>\(\)\(  
  devtools\( // 1\. Connect to DevTools \(must be outermost or just inside persist\)  
    persist\( // 2\. Persist state  
      \(set\) => \(\{  
        theme: 'light',  
        notificationsEnabled: true,  
        toggleTheme: \(\) => set\(\(state\) => \(\{ theme: state\.theme === 'light' ? 'dark' : 'light' \}\)\),  
        setNotifications: \(enabled\) => set\(\{ notificationsEnabled: enabled \}\),  
      \}\),  
      \{  
        name: 'app\-settings\-storage', // Name for the storage item  
        storage: createJSONStorage\(\(\) => localStorage\), // Or sessionStorage  
      \}  
    \),  
    \{ name: 'AppSettingsStore' \} // Name shown in DevTools  
  \)  
  // Optional: Wrap with immer for complex state updates  
  // immer\(\(set\) => \(\{ \.\.\. \}\)\)  
\);  


## __Async Operations__

- Handle async logic directly within store actions\.
- Use isLoading, error states to track request status\.

// Example Async Action  
interface DataState \{  
  items: string\[\];  
  isLoading: boolean;  
  error: string | null;  
  fetchItems: \(\) => Promise<void>;  
\}  
  
export const useDataStore = create<DataState>\(\(set\) => \(\{  
  items: \[\],  
  isLoading: false,  
  error: null,  
  fetchItems: async \(\) => \{  
    set\(\{ isLoading: true, error: null \}\);  
    try \{  
      // const response = await fetch\('/api/items'\);  
      // if \(\!response\.ok\) throw new Error\('Network response was not ok'\);  
      // const fetchedItems = await response\.json\(\);  
      const fetchedItems = await new Promise<string\[\]>\(resolve => setTimeout\(\(\) => resolve\(\['Item 1', 'Item 2'\]\), 1000\)\); // Mock API call  
      set\(\{ items: fetchedItems, isLoading: false \}\);  
    \} catch \(err: any\) \{  
      set\(\{ isLoading: false, error: err\.message || 'Failed to fetch items' \}\);  
    \}  
  \},  
\}\)\);  


## __Handling Complex Async Flows \(New Section\)__

For actions involving multiple dependent async steps:

interface ComplexFlowState \{  
  step1Data: any | null;  
  step2Data: any | null;  
  finalResult: any | null;  
  isLoading: boolean;  
  error: string | null;  
  executeComplexFlow: \(initialParam: string\) => Promise<void>;  
\}  
  
export const useComplexFlowStore = create<ComplexFlowState>\(\(set, get\) => \(\{  
  step1Data: null,  
  step2Data: null,  
  finalResult: null,  
  isLoading: false,  
  error: null,  
  executeComplexFlow: async \(initialParam\) => \{  
    set\(\{ isLoading: true, error: null, step1Data: null, step2Data: null, finalResult: null \}\);  
    try \{  
      // Step 1  
      // const data1 = await api\.step1\(initialParam\);  
      const data1 = await new Promise<any>\(resolve => setTimeout\(\(\) => resolve\(\{ id: '123', value: initialParam \}\), 500\)\);  
      set\(\{ step1Data: data1, isLoading: true \}\); // Keep loading true  
  
      // Step 2 \(depends on Step 1\)  
      // const data2 = await api\.step2\(data1\.id\);  
       const data2 = await new Promise<any>\(resolve => setTimeout\(\(\) => resolve\(\{ related: data1\.id, detail: 'Details' \}\), 500\)\);  
      set\(\{ step2Data: data2, isLoading: true \}\); // Keep loading true  
  
      // Step 3 \(Final processing\)  
      // const result = processData\(data1, data2\);  
       const result = \{ combined: \`$\{data1\.value\} \- $\{data2\.detail\}\` \};  
      set\(\{ finalResult: result, isLoading: false \}\); // Final state, loading false  
  
    \} catch \(err: any\) \{  
      set\(\{ isLoading: false, error: err\.message || 'Complex flow failed' \}\);  
      // Consider resetting intermediate states on error if needed  
      // set\(\{ step1Data: null, step2Data: null, finalResult: null, isLoading: false, error: \.\.\. \}\);  
    \}  
  \},  
\}\)\);  
  


## __Best Practices__

- __Immutability:__ Always update state immutably \(e\.g\., using spread syntax \{\.\.\.state\}\)\.
- __Single Source of Truth:__ Avoid duplicating state across multiple stores\. Derive state where possible\.
- __Context API:__ Use React Context primarily for global themes, user settings, or dependency injection that rarely change, not for frequently updated application state\.
- __Testing:__ Test store logic \(actions, selectors\) independently using Jest or Vitest\. Mock async operations or middleware effects as needed\.

