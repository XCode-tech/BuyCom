'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRouter } from 'next/navigation'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

interface Company {
    id: number;
    gstin: string;
    legal_name: string;
    state: string;
    result: string;
    fetch_date?: string;
    registration_date?: string;
    last_update?: string;
    trade_name?: string;
    company_type?: string;
    delayed_filling?: string;
    Delay_days?: string;
    address?: string;
    return_status?: string;
    month?: string;
    year?: string;
    date_of_filing?: string;
    return_type?: string;
}

export default function UserDashboard() {
    const [allData, setAllData] = useState<Company[]>([])
    const [displayData, setDisplayData] = useState<Company[]>([])
    const [currentPage, setCurrentPage] = useState(1)
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isAdmin, setIsAdmin] = useState(false)
    const [itemsPerPage] = useState(10)
    const router = useRouter()
    const [filters, setFilters] = useState({
        legal_name: '',
        gstin: '',
        state: '',
        status: 'all',
    })
    const [searchQuery, setSearchQuery] = useState('')

    useEffect(() => {
        const token = localStorage.getItem('auth_tokens')
        const userRole = localStorage.getItem('user_role')

        if (!token || userRole !== 'admin') {
            router.push('/')
        } else {
            setIsAuthenticated(true)
            setIsAdmin(true)
        }
    }, [router])

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${API_URL}/companies/`)
                const data: Company[] = await response.json()

                const uniqueData: Company[] = Array.from(new Map(data.map(item => [item.gstin, item])).values())
                setAllData(uniqueData)
            } catch (error) {
                console.error("Error fetching data:", error)
            }
        }
        fetchData()
    }, [])

    useEffect(() => {
        let filteredData = allData.filter(item =>
            (filters.legal_name === '' || item.legal_name.toLowerCase().includes(filters.legal_name.toLowerCase())) &&
            (filters.gstin === '' || item.gstin.toLowerCase().includes(filters.gstin.toLowerCase())) &&
            (filters.state === '' || item.state.toLowerCase().includes(filters.state.toLowerCase())) &&
            (filters.status === 'all' || item.result === filters.status)
        )

        if (searchQuery) {
            filteredData = filteredData.filter(item =>
                item.gstin.toLowerCase().includes(searchQuery.toLowerCase())
            )
        }

        setDisplayData(filteredData)
        setCurrentPage(1)
    }, [filters, searchQuery, allData])

    const handleFilterChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }

    const paginate = (pageNumber: number) => setCurrentPage(pageNumber)

    const indexOfLastItem = currentPage * itemsPerPage
    const indexOfFirstItem = indexOfLastItem - itemsPerPage
    const currentItems = displayData.slice(indexOfFirstItem, indexOfLastItem)

    if (!isAuthenticated || !isAdmin) {
        return <div>Loading...</div>
    }

    return (
        <>
            <form onSubmit={(e) => e.preventDefault()} className="flex space-x-4 mb-6">
                <Input
                    type="text"
                    placeholder="Enter GST Number"
                    className="flex-grow"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Button type="submit">Search</Button>
            </form>

            <div className="mb-4 grid grid-cols-4 gap-4">
                <Input
                    placeholder="Filter by Company Name"
                    value={filters.legal_name}
                    onChange={(e) => handleFilterChange('legal_name', e.target.value)}
                />
                <Input
                    placeholder="Filter by GSTIN"
                    value={filters.gstin}
                    onChange={(e) => handleFilterChange('gstin', e.target.value)}
                />
                <Input
                    placeholder="Filter by State"
                    value={filters.state}
                    onChange={(e) => handleFilterChange('state', e.target.value)}
                />
                <Select onValueChange={(value) => handleFilterChange('status', value)} value={filters.status}>
                    <SelectTrigger>
                        <SelectValue placeholder="Filter by Status" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="Pass">Pass</SelectItem>
                        <SelectItem value="Fail">Fail</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className='text-center'>Company Name</TableHead>
                        <TableHead className='text-center'>GSTIN</TableHead>
                        <TableHead className='text-center'>State</TableHead>
                        <TableHead className='text-center'>Fetch Date</TableHead>
                        <TableHead className='text-center'>AVG. DELAY DAYS</TableHead>
                        <TableHead className='text-center'>% DELAYED FILLING</TableHead>
                        <TableHead className='text-center'>Status</TableHead>
                        <TableHead className='text-center'>Action</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {currentItems.map((item) => (
                        <TableRow key={item.id}>
                            <TableCell className='text-center'>{item.legal_name}</TableCell>
                            <TableCell className='text-center'>{item.gstin}</TableCell>
                            <TableCell className='text-center'>{item.state}</TableCell>
                            <TableCell className='text-center'>{item.fetch_date}</TableCell>
                            <TableCell className='text-center'>{item.Delay_days}</TableCell>
                            <TableCell className='text-center'>{item.Delay_days}%</TableCell>
                            <TableCell className='text-center'>{item.result}</TableCell>
                            <TableCell className='text-center'>
                                <Button variant="outline" size="sm">Download</Button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>

            <div className="mt-4 flex justify-center space-x-2">
                <Button onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1}>
                    Previous
                </Button>
                {Array.from({ length: Math.ceil(displayData.length / itemsPerPage) }).map((_, index) => (
                    <Button
                        key={index}
                        variant={currentPage === index + 1 ? "default" : "outline"}
                        onClick={() => paginate(index + 1)}
                    >
                        {index + 1}
                    </Button>
                ))}
                <Button
                    onClick={() => paginate(currentPage + 1)}
                    disabled={currentPage === Math.ceil(displayData.length / itemsPerPage)}
                >
                    Next
                </Button>
            </div>

        </>
    )
}
