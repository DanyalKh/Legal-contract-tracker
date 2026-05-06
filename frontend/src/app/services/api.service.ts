import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {

  private baseUrl = '/api';

  constructor(private http: HttpClient) {}

  getContracts(search?: string, clauseTypeId?: number, groupByClause?: boolean): Observable<any> {
    let params: any = {};
    if (search) params.search = search;
    if (clauseTypeId) params.clause_type_id = clauseTypeId;
    if (groupByClause) params.group_by_clause = groupByClause;
    
    return this.http.get(`${this.baseUrl}/contracts`, { params });
  }

  getContract(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/contracts/${id}`);
  }

  uploadContract(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(`${this.baseUrl}/contracts`, formData);
  }

  deleteContract(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/contracts/${id}`);
  }

  downloadContract(id: number): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/contracts/${id}/download`, {
      responseType: 'blob'
    });
  }

  labelSentence(sentenceId: number, clauseTypeId: number): Observable<any> {
    return this.http.post(
      `${this.baseUrl}/sentences/${sentenceId}/label`,
      { clause_type_id: clauseTypeId }
    );
  }

  labelled_count(startDate?: string, endDate?: string): Observable<any> {
    let params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.get(`${this.baseUrl}/sentences/label`, { params });
  }

  removeLabel(sentenceId: number): Observable<any> {
    return this.http.delete(
      `${this.baseUrl}/sentences/${sentenceId}/label`
    );
  }

  getClauseTypes(): Observable<any> {
    return this.http.get(`${this.baseUrl}/clause-types`);
  }
}