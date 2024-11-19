'use client'

import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"

export default function AuthenticatedLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const router = useRouter()

    const handleLogout = () => {
        // Clear the authentication token or session
        localStorage.removeItem('auth_tokens')  // If you're using localStorage
        localStorage.removeItem('user_role') // If you're using sessionStorage
        
        // Optionally, clear cookies if you're using them
        document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'

        // Redirect to login page
        router.push('/') // Change '/login' to your actual login page route
    }

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex">
                            <div className="flex-shrink-0 flex items-center">
                                <span className="text-2xl font-bold">GST Search Portal</span>
                            </div>
                        </div>
                        <div className="flex items-center">
                            <Button variant="ghost" onClick={handleLogout}>Logout</Button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                {children}
            </main>
        </div>
    )
}
