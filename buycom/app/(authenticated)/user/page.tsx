'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRouter } from 'next/navigation'
import API_URL from '@/config'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import jsPDF from 'jspdf'
import 'jspdf-autotable'


import { UserOptions as AutoTableUserOptions } from 'jspdf-autotable'

interface AutoTableOptions extends Omit<AutoTableUserOptions, 'theme'> {
    startY: number;
    head: string[][];
    body: string[][];
    theme?: 'striped' | 'grid' | 'plain' | 'css';
}

declare module 'jspdf' {
    interface jsPDF {
        autoTable: (options: AutoTableOptions) => jsPDF;
        lastAutoTable?: {
            finalY: number;
        };
    }
}

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



    // **New Filter Function**
    const filterDataForPDF = async (gstin: string): Promise<Company | null> => {
        try {
            const response = await fetch(`${API_URL}/companies/${gstin}/`)
            if (response.ok) {
                const data = await response.json()
                // const filteredData = data.find(item => item.gstin === gstin)
                
                return data || null

            } else {
                console.error("Failed to fetch company data")
                return null
            }
        } catch (error) {
            console.error("Error fetching company data:", error)
            return null
        }
    }

    const getMonthName = (monthNumber: string): string => {
        const months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        const monthIndex = parseInt(monthNumber, 10) - 1;
        return months[monthIndex] || 'N/A';
    };

    // **Updated Generate PDF Function**
    const generatePDF = async (gstin: string) => {
        const items = await filterDataForPDF(gstin);
        console.log("items : ", items);
    
        // Check if items is an array and not empty
        if (!Array.isArray(items) || items.length === 0) {
            console.error("No data found for the provided GSTIN or array is empty");
            return;
        }
    
        // Create a single PDF document
        const doc = new jsPDF();
        doc.setFontSize(14);
        doc.text('COMPANY GST3B SUMMARY', 14, 15);
        doc.setFontSize(10);
    
        // Define summary table data for the first item
        const summaryTableData = [
            ['GSTIN', items[0].gstin || 'N/A', 'STATUS', items[0].return_status || 'N/A'],
            ['LEGAL NAME', items[0].legal_name || 'N/A', 'REG. DATE', items[0].registration_date || 'N/A'],
            ['TRADE NAME', items[0].trade_name || 'N/A', 'LAST UPDATE DATE', items[0].last_update || 'N/A'],
            ['COMPANY TYPE', items[0].company_type || 'N/A', 'STATE', items[0].state || 'N/A'],
            ['% DELAYED FILLING', items[0].delayed_filling || 'N/A', 'AVG. DELAY DAYS', items[0].Delay_days || 'N/A'],
            ['Address', items[0].address || 'N/A', 'Result', items[0].result || 'N/A'],
        ];
    
        // Add the summary table
        doc.autoTable({
            startY: 20, // Starting position of the table
            head: [['', '', '', '']],
            body: summaryTableData,
            theme: 'grid',
            headStyles: { fillColor: [230, 230, 230] },
            styles: { fontSize: 10, cellPadding: 3, textColor: [0, 0, 0] },
            columnStyles: { 0: { cellWidth: 45 }, 1: { cellWidth: 70 }, 2: { cellWidth: 45 }, 3: { cellWidth: 30 } },
        });
    
        // Calculate yPos for the next table
        const yPos = doc.lastAutoTable?.finalY ? doc.lastAutoTable.finalY + 10 : 20;
    
        // Initialize an array for filing details
        const filingDetails: string[][] = [];
        items.forEach((item) => {
            if (item) {
                filingDetails.push([
                    item.year || 'N/A',
                    item.month || 'N/A', // We'll sort this later based on numerical values
                    item.return_type || 'N/A',
                    item.date_of_filing || 'N/A',
                    item.delayed_filling || 'N/A',
                    item.Delay_days || 'N/A'
                ]);
            }
        });
    
        // Sort the filing details by year and month in descending order
        filingDetails.sort((a, b) => {
            const yearA = parseInt(a[0], 10);
            const yearB = parseInt(b[0], 10);
            const monthA = parseInt(a[1], 10);
            const monthB = parseInt(b[1], 10);
    
            // First compare by year (descending order)
            if (yearA > yearB) return -1;
            if (yearA < yearB) return 1;
    
            // If years are the same, compare by month (descending order)
            if (monthA > monthB) return -1;
            if (monthA < monthB) return 1;
    
            return 0;
        });
    
        // Convert month number to month name after sorting
        const sortedFilingDetails = filingDetails.map(item => [
            item[0], // Year
            getMonthName(item[1]), // Month converted to name
            item[2], // Return Type
            item[3], // Date of Filing
            item[4], // Delayed Filing
            item[5]  // Delay Days
        ]);
    
        // Add the filing details table
        doc.autoTable({
            startY: yPos, // Start from the calculated position after the first table
            head: [['Year', 'Month', 'Return Type', 'Date of Filing', 'Delayed Filing', 'Delay Days']],
            body: sortedFilingDetails,
            theme: 'grid',
            headStyles: { fillColor: [230, 230, 230] },
            styles: { fontSize: 10, cellPadding: 3, textColor: [0, 0, 0] },
            columnStyles: { 0: { cellWidth: 30 }, 1: { cellWidth: 30 }, 2: { cellWidth: 30 }, 3: { cellWidth: 30 }, 4: { cellWidth: 35 }, 5: { cellWidth: 30 } },
        });
    
        // Save the generated PDF with a common file name
        doc.save(`${gstin}_summary.pdf`);
    };
    

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
                                {/* <Button variant="outline" size="sm">Download</Button> */}
                                <Button variant="outline" size="sm" onClick={() => generatePDF(item.gstin)} className="mr-2">Download</Button>
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
